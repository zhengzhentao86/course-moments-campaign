import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1] / 'scripts' / 'campaign.py'
spec=importlib.util.spec_from_file_location('campaign',SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class CampaignTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.work=self.root/'course'
  m.init_workspace(self.work,'sample-course','示例课')
 def tearDown(self):self.temp.cleanup()
 def feedback(self,**kw):
  d=dict(id='f1',course_id='sample-course',kind='editorial',scope='course',source_ref='local-evidence:1',summary='需要具体',action='增加工作动作',rule_key='detail');d.update(kw);return d
 def manifest(self):
  p=dict(id=1,title='主题',text='正文',audience_problem='问题',course_method='方法',practical_output='产物',poster_prompt='提示词',source_refs=['brief:1'],image='posters/01.png',copy_reviewed=True,visual_reviewed=True)
  d=dict(expected_count=1,posts=[p]);path=self.root/'campaign.json';return d,path
 def save(self,d,p):m.atomic_json(p,d)
 def test_calendar_cross_year(self):
  rows=m.calendar('2027-01-05',10);self.assertEqual(rows[0],{'days':10,'publish_date':'2026-12-26'});self.assertEqual(rows[-1]['publish_date'],'2027-01-04')
 def test_calendar_leap_year(self):self.assertEqual(m.calendar('2028-03-01',1)[0]['publish_date'],'2028-02-29')
 def test_calendar_bad_count(self):
  with self.assertRaises(ValueError):m.calendar('2027-01-05',0)
 def test_init_no_overwrite(self):
  with self.assertRaises(ValueError):m.init_workspace(self.work,'sample-course','新名')
 def test_feedback_idempotency(self):
  a=self.feedback();m.record_feedback(self.work,a);self.assertIn('duplicate_skipped',m.record_feedback(self.work,a));self.assertEqual(len((self.work/'feedback.jsonl').read_text().splitlines()),1)
 def test_feedback_wrong_course(self):
  with self.assertRaises(ValueError):m.record_feedback(self.work,self.feedback(course_id='another'))
 def test_no_implicit_global_preference(self):
  with self.assertRaises(ValueError):m.record_feedback(self.work,self.feedback(scope='cross_course'))
 def test_supersedes_history_retained(self):
  m.record_feedback(self.work,self.feedback());m.record_feedback(self.work,self.feedback(id='f2',supersedes=['f1'],action='调整动作'))
  self.assertEqual(len((self.work/'feedback.jsonl').read_text().splitlines()),2)
 def test_no_supersede_other_rule(self):
  m.record_feedback(self.work,self.feedback())
  with self.assertRaises(ValueError):m.record_feedback(self.work,self.feedback(id='f2',rule_key='color',supersedes=['f1']))
 def test_draft_is_not_final(self):
  d,p=self.manifest();self.save(d,p);self.assertFalse(m.check_campaign(p,True));self.assertTrue(m.check_campaign(p))
 def test_missing_review(self):
  d,p=self.manifest();d['posts'][0]['visual_reviewed']=False;self.save(d,p);self.assertTrue(any('visual_reviewed' in x for x in m.check_campaign(p)))
 def test_date_mismatch(self):
  d,p=self.manifest();d.update(mode='countdown',start_date='2027-01-05');d['posts'][0].update(days=1,publish_date='2027-01-03');self.save(d,p);self.assertTrue(any('mismatch' in x for x in m.check_campaign(p,True)))
 def test_image_escape(self):
  d,p=self.manifest();d['posts'][0]['image']='../secret.png';self.save(d,p);self.assertTrue(any('within' in x for x in m.check_campaign(p)))
 def test_duplicate_id(self):
  d,p=self.manifest();d['posts'].append(dict(d['posts'][0]));d['expected_count']=2;self.save(d,p);self.assertTrue(any('duplicate id' in x for x in m.check_campaign(p,True)))

if __name__=='__main__':unittest.main(verbosity=2)
