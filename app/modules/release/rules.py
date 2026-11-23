from decimal import Decimal
from app.coerce import money

def decide(row):
    billable=Decimal(row['billable_kg']);due=Decimal(row['due'])
    base={'ticket':row['ticket'],'version':row['version'],'billable_kg':row['billable_kg'],
        'amount':row['amount'],'paid':row['paid'],'due':row['due']}
    if due<=0:
        return {**base,'release_kg':row['billable_kg'],'withheld_kg':'0.000','status':'可放行','code':'RELEASED'}
    return {**base,'release_kg':'0.000','withheld_kg':format(billable,'f'),'status':'暂缓','code':'WITHHELD_UNPAID'}

def blocked(state):
    paid={}
    for row in state['settlements']:
        paid[row['ticket']]=max(paid.get(row['ticket'],Decimal(0)),Decimal(row['paid']))
    return [{'ticket':c['ticket'],'version':c.get('version',''),'billable_kg':'','amount':'',
        'paid':money(paid.get(c['ticket'],Decimal(0))),'due':'','release_kg':'0.000','withheld_kg':'',
        'status':'不可放行','code':c['code']} for c in state['version_conflicts']]

def release_balance(rows,final):
    releasable=[r for r in rows if r['status']=='可放行']
    released=sum((Decimal(r['release_kg']) for r in releasable),Decimal(0))
    withheld=sum((Decimal(r['withheld_kg']) for r in rows if r['status']=='暂缓'),Decimal(0))
    total=sum((Decimal(r['billable_kg']) for r in final),Decimal(0))
    settled=sum((Decimal(r['amount']) for r in releasable),Decimal(0))
    over=any(Decimal(r['release_kg'])>Decimal(r['billable_kg']) for r in releasable)
    return {'released_kg':format(released,'f'),'withheld_kg':format(withheld,'f'),
        'settled_amount':money(settled),'quantity_balanced':released+withheld==total,
        'over_limit':over,'balanced':released+withheld==total and not over}

def apply(state):
    rows=[decide(r) for r in state['final']]+blocked(state)
    summary=release_balance(rows,state['final'])
    state['release']={'rows':rows,**summary}
    state['views']['release']={'title':'提货放行','rows':rows,'metrics':{
        '放行票':sum(1 for r in rows if r['status']=='可放行'),
        '暂缓量_kg':summary['withheld_kg'],'已结清_CNY':summary['settled_amount']}}
