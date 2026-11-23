import hashlib, json

def archive_decision(state):
    release=state.get('release',{})
    ready=(state['balance']['row_balanced'] and state['balance']['money_balanced']
        and not state['balance']['blocked'] and release.get('balanced',False))
    seal=hashlib.sha256(json.dumps(state['final'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return {'seal':seal,'status':'可归档' if ready else '待处理','tickets':len(state['final']),
        'reasons':len(state['quarantine']),'release_balanced':release.get('balanced',False),
        'withheld_kg':release.get('withheld_kg','0')}

def apply(state):
    state['archive']=archive_decision(state)
    state['views']['archive']={'title':'结算封存','rows':state['version_audit'],'metrics':{'封存票':state['archive']['tickets'],'隔离证据':len(state['quarantine']),'暂缓量_kg':state['archive']['withheld_kg'],'状态':state['archive']['status']}}
