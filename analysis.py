"""Run from project root: python analysis.py. Source: UCI Online Retail, Chen (2015)."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mlxtend.frequent_patterns import fpgrowth, association_rules
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
raw=pd.read_excel(ROOT/'data'/'Online Retail.xlsx',dtype={'InvoiceNo':str,'StockCode':str})
audit=[]
df=raw.copy()
def exclude(reason,mask):
 global df
 audit.append({'step':reason,'removed_rows':int(mask.sum())});df=df.loc[~mask].copy()
exclude('Missing invoice product or date',df[['InvoiceNo','StockCode','InvoiceDate']].isna().any(axis=1))
exclude('Cancellation invoice',df.InvoiceNo.str.upper().str.startswith('C'))
exclude('Nonpositive or missing quantity or price',~((df.Quantity>0)&(df.UnitPrice>0)))
# Standard merchandise identifiers: five digits, optionally followed by letters.
exclude('Nonmerchandise or atypical product code',~df.StockCode.str.fullmatch(r'\d{5}[A-Za-z]*'))
exclude('Exact duplicate row',df.duplicated())
pd.DataFrame(audit).to_csv(OUT/'cleaning_audit.csv',index=False)
baskets=df.groupby('InvoiceNo').agg(date=('InvoiceDate','min'),items=('StockCode',lambda s:tuple(sorted(set(s)))))
baskets['size']=baskets['items'].map(len)
baskets.to_pickle(OUT/'baskets.pkl')
names=df.dropna(subset=['Description']).groupby('StockCode').Description.agg(lambda s:s.value_counts().index[0]).to_dict()
train=baskets[baskets.date<'2011-08-01'];valid=baskets[(baskets.date>='2011-08-01')&(baskets.date<'2011-10-01')];test=baskets[baskets.date>='2011-10-01']
def fit(frame,support,lift):
 counts=pd.Series([x for b in frame['items'] for x in b]).value_counts()
 # Product restriction chosen exclusively from the fitting period.
 products=counts.head(300).index.tolist();idx={p:i for i,p in enumerate(products)}
 matrix=np.zeros((len(frame),len(products)),dtype=bool)
 for row,b in enumerate(frame['items']):
  for p in b:
   if p in idx:matrix[row,idx[p]]=True
 freq=fpgrowth(pd.DataFrame(matrix,columns=products),min_support=support,use_colnames=True,max_len=2)
 rules=association_rules(freq,metric='lift',min_threshold=lift) if len(freq) else pd.DataFrame()
 if len(rules):
  rules=rules[(rules.antecedents.map(len)==1)&(rules.consequents.map(len)==1)].copy()
  rules['a']=rules.antecedents.map(lambda s:next(iter(s)));rules['b']=rules.consequents.map(lambda s:next(iter(s)))
 return rules,counts

def evaluate(frame,rules,counts):
 lookup={}
 if len(rules):
  for r in rules.itertuples():lookup.setdefault(r.a,[]).append((r.b,r.confidence,r.lift,r.support))
 rows=[];known=set(counts.index)
 for invoice,r in frame.iterrows():
  if len(r['items'])<2:continue
  # Stable holdout independent of dataframe ordering and model settings.
  pos=int(hashlib.sha256(str(invoice).encode()).hexdigest()[:12],16)%len(r['items'])
  hidden=r['items'][pos];visible=set(r['items'])-{hidden};scores={}
  for a in visible:
   for b,c,l,s in lookup.get(a,[]):
    if b not in visible:scores[b]=max(scores.get(b,(0,0,0)),(c,l,s))
  rec=sorted(scores,key=lambda x:(-scores[x][0],-scores[x][1],-scores[x][2],x))[:5]
  baseline=[p for p in counts.index if p not in visible][:5]
  rows.append({'invoice':invoice,'hidden':hidden,'rule_hit':int(hidden in rec),'baseline_hit':int(hidden in baseline),'covered':int(bool(rec)),'known_target':int(hidden in known),'recommendations':'|'.join(rec),'visible_items':'|'.join(sorted(visible))})
 return pd.DataFrame(rows)
tuning=[]
for s in [.005,.01]:
 for l in [1.,1.5,2.]:
  rules,c=fit(train,s,l);ev=evaluate(valid,rules,c)
  tuning.append({'support':s,'lift':l,'rules':len(rules),'hit_rate':ev.rule_hit.mean(),'coverage':ev.covered.mean(),'baseline':ev.baseline_hit.mean()})
tuning=pd.DataFrame(tuning).sort_values(['hit_rate','coverage','support','lift'],ascending=[False,False,False,False]);tuning.to_csv(OUT/'validation.csv',index=False)
best=tuning.iloc[0];dev=baskets[baskets.date<'2011-10-01'];rules,counts=fit(dev,float(best.support),float(best.lift));ev=evaluate(test,rules,counts);ev.to_csv(OUT/'test_predictions.csv',index=False)
if len(rules):
 rules['antecedent_name']=rules.a.map(names);rules['consequent_name']=rules.b.map(names)
 rules.drop(columns=['antecedents','consequents']).sort_values(['lift','confidence'],ascending=False).to_csv(OUT/'rules.csv',index=False)
rng=np.random.default_rng(42);delta=(ev.rule_hit-ev.baseline_hit).to_numpy();boots=np.array([rng.choice(delta,len(delta),replace=True).mean() for _ in range(2000)])
summary={'raw_rows':len(raw),'clean_rows':len(df),'missing_customer_rows_retained':int(df.CustomerID.isna().sum()),'baskets':len(baskets),'products':df.StockCode.nunique(),'train_baskets':len(train),'validation_baskets':len(valid),'test_baskets':len(test),'eligible_test_baskets':len(ev),'chosen_support':float(best.support),'chosen_lift':float(best.lift),'rules':len(rules),'rule_hit_at_5':float(ev.rule_hit.mean()),'baseline_hit_at_5':float(ev.baseline_hit.mean()),'coverage':float(ev.covered.mean()),'unseen_targets':int((ev.known_target==0).sum()),'difference_ci95':np.quantile(boots,[.025,.975]).tolist(),'min_date':str(df.InvoiceDate.min()),'max_date':str(df.InvoiceDate.max())}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
plt.rcParams.update({'figure.dpi':160,'axes.spines.top':False,'axes.spines.right':False})
def save(name):plt.tight_layout();plt.savefig(OUT/name,bbox_inches='tight');plt.close()
plt.figure(figsize=(7,3.5));df.set_index('InvoiceDate').resample('MS').InvoiceNo.nunique().plot.bar(color='#245e91');plt.ylabel('Distinct valid invoices');plt.xlabel('Month');plt.xticks(rotation=45);save('01_monthly_invoices.png')
plt.figure(figsize=(7,3.5));baskets['size'].clip(upper=100).hist(bins=30,color='#245e91');plt.xlabel('Distinct products per basket (100 includes larger baskets)');plt.ylabel('Baskets');save('02_basket_sizes.png')
plt.figure(figsize=(7,3.5));top=counts.head(10);plt.barh([str(names.get(p,p))[:38] for p in top.index][::-1],top.values[::-1],color='#245e91');plt.xlabel('Development baskets containing product');save('03_popular_products.png')
plt.figure(figsize=(6,3.5));plt.bar(['Association rules','Popular products'],[summary['rule_hit_at_5']*100,summary['baseline_hit_at_5']*100],color=['#245e91','#c17f28']);plt.ylabel('Test hit rate at 5 (%)');save('04_recommendation_performance.png')
plt.figure(figsize=(6,3.5));plt.bar(['Received recommendations','No rule recommendation'],[ev.covered.sum(),len(ev)-ev.covered.sum()],color=['#245e91','#999999']);plt.ylabel('Eligible test baskets');save('05_recommendation_coverage.png')

