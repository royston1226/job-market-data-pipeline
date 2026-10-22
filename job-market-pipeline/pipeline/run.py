"""Parquet -> raw MongoDB -> transformation -> PostgreSQL + Elasticsearch."""
import os, json, time, hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq
from pymongo import MongoClient, ReplaceOne
import psycopg
from elasticsearch import Elasticsearch, helpers
from pipeline.transform import transform

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['id','job_id','company_id','title','department','employment_type',
          'workplace_type','country','apply_url','status','is_remote','posted_at',
          'fetched_time','close_time','duration_days','quality_flags']
MAPPING = {'properties': {
    **{k:{'type':'keyword'} for k in ['id','job_id','country','status','workplace_type','employment_type','quality_flags']},
    'title': {'type':'text'}, 'department': {'type':'text'},
    'company_id': {'type':'long'}, 'is_remote': {'type':'boolean'},
    **{k:{'type':'date'} for k in ['posted_at','fetched_time','close_time']},
    'duration_days': {'type':'double'}, 'apply_url': {'type':'keyword','index':False}
}}

def search_document(row):
    return {k:v.isoformat() if isinstance(v,datetime) else v for k,v in row.items()}

def write_rejection(report, run_id, document, error):
    """Write only rejection metadata, making each entry visible immediately."""
    entry = {
        'run_id': run_id,
        'source_file': document['source_file'],
        'source_record_id': document['record'].get('id'),
        'error_type': type(error).__name__,
        'reason': (str(error) or type(error).__name__)[:500],
    }
    report.write(json.dumps(entry, ensure_ascii=False) + '\n')
    report.flush()


def main():
    run_id = datetime.now(timezone.utc).isoformat()
    (ROOT/'reports').mkdir(exist_ok=True)
    # Truncate before validation or service setup, so stale rejections never
    # masquerade as results from this invocation (including failed runs).
    with (ROOT/'reports/rejected_records.jsonl').open('w', encoding='utf-8') as rejections:
        run_pipeline(run_id, rejections)


def run_pipeline(run_id, rejections):
    limit = int(os.getenv('ROW_LIMIT','25000'))
    if limit < 0: raise ValueError('ROW_LIMIT must be >= 0')
    files = sorted((ROOT/'data').glob('*.parquet'))
    if not files: raise FileNotFoundError('Put jobs Parquet files in data/')
    stats = Counter(rejected_records=0); timings = Counter(); start = time.perf_counter()
    mongo = MongoClient(os.environ['MONGO_URI'], tz_aware=True)
    collection = mongo.jobs.raw_jobs
    es = Elasticsearch(os.environ['ELASTIC_URL'], request_timeout=60)
    if not es.indices.exists(index='jobs'):
        es.indices.create(index='jobs', mappings=MAPPING)
    with psycopg.connect(os.environ['POSTGRES_DSN']) as conn:
        conn.execute((ROOT/'sql/schema.sql').read_text()); conn.commit()
        seen = set()
        for file in files:
            parquet = pq.ParquetFile(file)
            for batch in parquet.iter_batches(batch_size=1000):
                rows = batch.to_pylist()
                if limit: rows = rows[:max(0,limit-stats['records_read'])]
                if not rows: break
                t=time.perf_counter(); operations=[]; keys=[]
                for offset, raw in enumerate(rows):
                    stats['records_read']+=1
                    key = raw.get('id') or 'invalid:'+hashlib.sha256((file.name+str(stats['records_read'])).encode()).hexdigest()
                    if key in seen:
                        stats['duplicate_ids']+=1
                        continue
                    seen.add(key); keys.append(key)
                    operations.append(ReplaceOne({'_id':key}, {'_id':key,'record':raw,
                        'source_file':file.name,'run_id':run_id}, upsert=True))
                if operations: collection.bulk_write(operations, ordered=True)
                timings['mongo_seconds']+=time.perf_counter()-t
                t=time.perf_counter(); clean=[]
                # Transformation reads back the raw layer, rather than bypassing MongoDB.
                for document in collection.find({'_id':{'$in':keys},'run_id':run_id}):
                    try: row=transform(document['record'])
                    except (ValueError,TypeError,KeyError,OverflowError) as error:
                        write_rejection(rejections, run_id, document, error)
                        stats['rejected_records']+=1; continue
                    clean.append(row)
                    stats['records_cleaned']+=1
                    stats['missing_country']+=row['country'] is None
                    stats['quality_flag_count']+=len(row['quality_flags'])
                timings['transform_seconds']+=time.perf_counter()-t
                if clean:
                    t=time.perf_counter()
                    with conn.cursor() as cur:
                        cur.executemany('INSERT INTO companies VALUES (%s) ON CONFLICT DO NOTHING',
                                        [(x,) for x in sorted({r['company_id'] for r in clean})])
                        update=', '.join(f'{f}=EXCLUDED.{f}' for f in FIELDS if f!='id')
                        cur.executemany('INSERT INTO jobs ('+','.join(FIELDS)+') VALUES ('+
                            ','.join(['%s']*len(FIELDS))+') ON CONFLICT (id) DO UPDATE SET '+update,
                            [tuple(row[f] for f in FIELDS) for row in clean])
                    conn.commit(); timings['sql_seconds']+=time.perf_counter()-t
                    t=time.perf_counter()
                    count,_=helpers.bulk(es, ({'_index':'jobs','_id':row['id'],
                        '_source':search_document(row)} for row in clean), max_retries=3)
                    stats['records_indexed']+=count
                    timings['elastic_seconds']+=time.perf_counter()-t
                print(json.dumps(dict(stats)), flush=True)
                if limit and stats['records_read']>=limit: break
            if limit and stats['records_read']>=limit: break
        es.indices.refresh(index='jobs')
        sql_count=conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    report={'run_id':run_id,'status':'completed','row_limit':limit,'statistics':dict(stats),
        'timings':dict(timings),'total_seconds':time.perf_counter()-start,
        'stored_sql_jobs':sql_count,'stored_search_jobs':es.count(index='jobs')['count'],
        'source_files':[f.name for f in files]}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/latest_run.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    mongo.close(); es.close()

if __name__=='__main__': main()
