import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline import run
from pipeline.transform import transform


class RejectionReportingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "data").mkdir()
        (self.root / "data/source.parquet").touch()
        (self.root / "sql").mkdir()
        (self.root / "sql/schema.sql").write_text("SELECT 1;")
        self.report = self.root / "reports/rejected_records.jsonl"
        self.stored = {}
        self.collection = MagicMock()

        def store(operations, **kwargs):
            for operation in operations:
                document = copy.deepcopy(operation._doc)
                self.stored[document["_id"]] = document

        def find(query):
            return [self.stored[key] for key in query["_id"]["$in"]
                    if self.stored[key]["run_id"] == query["run_id"]]

        self.collection.bulk_write.side_effect = store
        self.collection.find.side_effect = find
        self.mongo = MagicMock()
        self.mongo.jobs.raw_jobs = self.collection
        self.conn = MagicMock()
        self.conn.execute.return_value.fetchone.return_value = (1,)
        self.es = MagicMock()
        self.es.count.return_value = {"count": 1}

    def raw(self, identifier="source:1", **changes):
        row = {"id": identifier, "title": "Engineer", "company_id": 5,
               "is_remote": False, "apply_url": "https://example.org/private"}
        row.update(changes)
        return row

    def invoke(self, batches, transformer=transform, bulk_error=None):
        parquet = MagicMock()
        parquet.iter_batches.return_value = [
            MagicMock(to_pylist=MagicMock(return_value=rows)) for rows in batches]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(run, "ROOT", self.root))
            stack.enter_context(patch.dict(run.os.environ, {
                "ROW_LIMIT": "0", "MONGO_URI": "mongodb://mock",
                "POSTGRES_DSN": "mock", "ELASTIC_URL": "http://mock"}))
            stack.enter_context(patch.object(run.pq, "ParquetFile", return_value=parquet))
            stack.enter_context(patch.object(run, "MongoClient", return_value=self.mongo))
            stack.enter_context(patch.object(run, "Elasticsearch", return_value=self.es))
            connect = stack.enter_context(patch.object(run.psycopg, "connect"))
            connect.return_value.__enter__.return_value = self.conn
            stack.enter_context(patch.object(run, "transform", side_effect=transformer))
            bulk = stack.enter_context(patch.object(run.helpers, "bulk", return_value=(1, [])))
            bulk.side_effect = bulk_error
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            run.main()
        return bulk

    def entries(self):
        return [json.loads(line) for line in self.report.read_text(encoding="utf-8").splitlines()]

    def summary(self):
        return json.loads((self.root / "reports/latest_run.json").read_text())

    def test_rejected_record_metadata_and_raw_preservation(self):
        invalid = self.raw(title=" ")
        bulk = self.invoke([[invalid, self.raw("source:2")]])
        entry, = self.entries()
        self.assertEqual(entry, {
            "run_id": self.summary()["run_id"], "source_file": "source.parquet",
            "source_record_id": "source:1", "error_type": "ValueError",
            "reason": "missing id or title"})
        self.assertEqual(self.stored["source:1"]["record"], invalid)
        self.assertEqual(self.summary()["statistics"]["rejected_records"], 1)
        self.assertEqual(self.summary()["statistics"]["records_cleaned"], 1)
        actions = list(bulk.call_args.args[1])
        self.assertEqual([action["_id"] for action in actions], ["source:2"])
        cursor = self.conn.cursor.return_value.__enter__.return_value
        jobs = cursor.executemany.call_args_list[1].args[1]
        self.assertEqual([row[0] for row in jobs], ["source:2"])
        self.assertNotIn("record", entry)
        self.assertNotIn(invalid["apply_url"], self.report.read_text())

    def test_rejections_are_visible_before_next_record_and_batch(self):
        seen = []

        def observe(raw):
            seen.append(len(self.entries()))
            return transform(raw)

        self.invoke([[self.raw(title=" ")],
                     [self.raw("source:2", is_remote="false"), self.raw("source:3")]],
                    transformer=observe)
        self.assertEqual(seen, [0, 1, 2])
        self.assertEqual(len(self.entries()), 2)
        self.assertEqual(self.summary()["statistics"]["rejected_records"], 2)

    def test_rerun_with_no_rejections_clears_previous_report(self):
        self.invoke([[self.raw(title=" ")]])
        self.assertEqual(len(self.entries()), 1)
        self.invoke([[self.raw()]])
        self.assertEqual(self.report.read_bytes(), b"")
        self.assertEqual(self.summary()["statistics"]["rejected_records"], 0)

    def test_rerun_replaces_previous_run_entries(self):
        self.invoke([[self.raw(title=" ")]])
        previous_run = self.entries()[0]["run_id"]
        self.invoke([[self.raw("source:new", is_remote="false")]])
        entry, = self.entries()
        self.assertNotEqual(entry["run_id"], previous_run)
        self.assertEqual(entry["run_id"], self.summary()["run_id"])
        self.assertEqual(entry["source_record_id"], "source:new")

    def test_missing_source_id_uses_null_not_synthetic_mongo_id(self):
        raw = self.raw(None)
        self.invoke([[raw]])
        entry, = self.entries()
        self.assertIsNone(entry["source_record_id"])
        self.assertEqual(entry["reason"], "missing id or title")
        document, = self.stored.values()
        self.assertTrue(document["_id"].startswith("invalid:"))
        self.assertEqual(document["record"], raw)

    def test_partial_report_survives_downstream_failure(self):
        with self.assertRaisesRegex(RuntimeError, "search unavailable"):
            self.invoke([[self.raw(title=" "), self.raw("source:2")]],
                        bulk_error=RuntimeError("search unavailable"))
        entry, = self.entries()
        self.assertEqual(entry["source_record_id"], "source:1")
        self.assertFalse((self.root / "reports/latest_run.json").exists())

    def test_failed_input_validation_still_clears_stale_report(self):
        self.report.parent.mkdir()
        self.report.write_text('old report\n')
        with patch.object(run, "ROOT", self.root), patch.dict(run.os.environ, {"ROW_LIMIT": "-1"}):
            with self.assertRaisesRegex(ValueError, "ROW_LIMIT"):
                run.main()
        self.assertEqual(self.report.read_bytes(), b"")

    def test_error_types_json_escaping_and_reason_bounds(self):
        self.report.parent.mkdir()
        document = {"source_file": "other.parquet", "record": self.raw("source:\u00e9")}
        errors = [ValueError("bad\nvalue"), TypeError("wrong type"), KeyError("company_id"),
                  OverflowError("out of range"), ValueError("x" * 600), ValueError()]
        with self.report.open("w", encoding="utf-8") as report:
            for count, error in enumerate(errors, start=1):
                run.write_rejection(report, "run:test", document, error)
                self.assertEqual(len(self.entries()), count)
        entries = self.entries()
        self.assertEqual([e["error_type"] for e in entries],
                         [type(e).__name__ for e in errors])
        self.assertEqual(entries[0]["reason"], "bad\nvalue")
        self.assertEqual(entries[0]["source_record_id"], "source:\u00e9")
        self.assertEqual(len(entries[-2]["reason"]), 500)
        self.assertEqual(entries[-1]["reason"], "ValueError")


if __name__ == "__main__":
    unittest.main()
