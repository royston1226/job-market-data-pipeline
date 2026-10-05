import unittest
from datetime import datetime,timezone
from pipeline.transform import transform
class TransformTests(unittest.TestCase):
 def raw(self,**changes):
  r={'id':'source:1','title':' Data   Engineer ','company_id':5,'is_remote':False,
     'employment_type':'Full time','posted_at':datetime(2026,1,1,tzinfo=timezone.utc),
     'close_time':datetime(2026,1,11,tzinfo=timezone.utc),'status':'CLOSED'}
  r.update(changes);return r
 def test_cleanup_and_duration(self):
  r=transform(self.raw());self.assertEqual(r['title'],'Data Engineer');self.assertEqual(r['duration_days'],10);self.assertEqual(r['employment_type'],'full-time')
 def test_missing_dates(self):
  self.assertIsNone(transform(self.raw(posted_at=None))['duration_days'])
 def test_negative_duration(self):
  r=transform(self.raw(close_time=datetime(2025,1,1,tzinfo=timezone.utc)))
  self.assertIsNone(r['duration_days']);self.assertIn('close_before_post',r['quality_flags'])
 def test_bad_required_fields(self):
  for changes in [{'title':' '},{'id':None},{'is_remote':'false'},{'company_id':'invalid'}]:
   with self.assertRaises(ValueError):transform(self.raw(**changes))
 def test_conflict_and_url(self):
  r=transform(self.raw(is_remote=True,workplace_type='ONSITE',apply_url='javascript:bad'))
  self.assertIsNone(r['apply_url']);self.assertEqual(len(r['quality_flags']),2)
 def test_open_has_no_closed_duration(self):
  self.assertIsNone(transform(self.raw(status='open'))['duration_days'])
if __name__=='__main__':unittest.main()
