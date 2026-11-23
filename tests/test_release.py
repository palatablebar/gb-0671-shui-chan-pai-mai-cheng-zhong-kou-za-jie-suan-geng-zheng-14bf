from app.modules.release.rules import decide, release_balance
from app.modules.archive.rules import archive_decision
from app.engine import evaluate
from copy import deepcopy
from decimal import Decimal

STALE_CSV='''id,ticket,kind,weight,unit,fish,price,rate,version,replaces,paid
00001gross,00001,gross,115,kg,黄鱼,12.30,0.05,1,,1000
00001tare,00001,tare,15,kg,黄鱼,12.30,0.05,1,,1000
00001gross2,00001,gross,120,kg,黄鱼,12.30,0.05,2,1,1000
00001tare2,00001,tare,15,kg,黄鱼,12.30,0.05,2,1,1000
00001gross3,00001,gross,121,kg,黄鱼,12.30,0.05,3,1,1000
00001tare3,00001,tare,15,kg,黄鱼,12.30,0.05,3,1,1000
'''

def test_release_covers_final_real(sample):
    rows=[r for r in sample['release']['rows'] if r['status']!='不可放行']
    assert [r['ticket'] for r in rows]==[r['ticket'] for r in sample['final']]
def test_unpaid_withheld_real(sample):
    assert sample['release']['released_kg']=='0'
    assert sample['release']['settled_amount']=='0.00'
    total=sum((Decimal(r['billable_kg']) for r in sample['final']),Decimal(0))
    assert Decimal(sample['release']['withheld_kg'])==total
def test_release_balanced_real(sample):
    assert sample['release']['quantity_balanced'] and sample['release']['balanced']
def test_settled_ticket_released():
    row={'ticket':'00001','version':'2','billable_kg':'104.500','amount':'1285.35','paid':'1285.35','due':'0.00'}
    d=decide(row);assert d['status']=='可放行' and d['release_kg']=='104.500' and d['withheld_kg']=='0.000'
def test_partial_payment_withheld():
    row={'ticket':'00001','version':'2','billable_kg':'104.500','amount':'1285.35','paid':'1168.50','due':'116.85'}
    d=decide(row);assert d['status']=='暂缓' and d['release_kg']=='0.000' and d['withheld_kg']=='104.500'
def test_over_release_detected(sample):
    rows=deepcopy(sample['release']['rows'])
    rows[0].update(status='可放行',release_kg=str(Decimal(rows[0]['billable_kg'])+Decimal('0.001')))
    assert release_balance(rows,sample['final'])['balanced'] is False
def test_quantity_imbalance_detected(sample):
    rows=deepcopy(sample['release']['rows']);rows.pop()
    assert release_balance(rows,sample['final'])['quantity_balanced'] is False
def test_rerun_no_extra_release(sample):
    again=evaluate()
    assert again['manifest']['run_id']==sample['manifest']['run_id']
    assert again['release']['rows']==sample['release']['rows']
def test_conflict_ticket_blocked_keeps_paid():
    s=evaluate({'csv_text':STALE_CSV})
    assert s['final']==[]
    row=[r for r in s['release']['rows'] if r['ticket']=='00001'][0]
    assert row['status']=='不可放行' and row['code']=='STALE_CORRECTION' and row['paid']=='1000.00'
    assert s['archive']['status']=='待处理'
def test_archive_blocked_by_release_imbalance(sample):
    s=deepcopy(sample);s['release']['balanced']=False
    assert archive_decision(s)['status']=='待处理'
def test_archive_carries_withheld_real(sample):
    assert sample['archive']['release_balanced'] is True
    assert sample['archive']['withheld_kg']==sample['release']['withheld_kg']
