from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def fail(msg): raise SystemExit('FAIL: '+msg)
def require(cond,msg):
    if not cond: fail(msg)

required=[
    'README.md','CLAIM_BOUNDARY.md','REPRODUCIBILITY.md','CERTIFICATE_SCHEMA.md','METHODS.md',
    'SOURCE_DOCUMENTS.json','results/frozen_summary.json','schema/rrc_certificate.schema.json',
    'experiments/baseline_detector_audit.py','results/baseline_detector_experiment_summary_v1_6.csv',
    'results/readability_transition_alpha_summary_v2_9.csv','results/readability_transition_resource_query_status_v2_9.csv',
    'results/market_strict_lattice_summary.json','certificates/market_primary_gmm_bootstrap_certificate_v2_1.json',
    'certificates/market_multinull_primary_gmm_audit_v2_3.json','certificates/market_multinull_focus_audit_v2_4.json',
    'paper/README.md','MANIFEST.json']
for rel in required: require((ROOT/rel).exists(), 'missing '+rel)

summary=json.load(open(ROOT/'results/frozen_summary.json'))
require(summary['manuscript_source_version']=='v3.7','wrong manuscript source version')
require(summary['core_claim']=='A detector output is not a regime claim by itself.','core claim drift')
require(summary['synthetic']['detector_benchmark_pairs']==20,'detector pair count')
require(summary['synthetic']['readability_transition_rows']==620,'source transition row count')
require(summary['synthetic']['resource_atlas_cells']==190,'resource atlas count')
require(summary['synthetic']['transition_not_physical_phase'] is True,'physical-phase boundary flag')

alpha=pd.read_csv(ROOT/'results/readability_transition_alpha_summary_v2_9.csv')
require(len(alpha)==31,'alpha summary row count')
require(set(alpha.n_seeds.astype(int))=={20},'alpha seed count')
require(float(alpha.loc[alpha.alpha==0,'mean_auc'].iloc[0]) < 0.55,'alpha=0 should remain unreadable')
require(float(alpha.loc[alpha.alpha==3.0,'mean_auc'].iloc[0]) > 0.99,'alpha=3 should be highly recoverable')

atlas=pd.read_csv(ROOT/'results/readability_transition_resource_query_status_v2_9.csv')
require(len(atlas)==190,'resource atlas cells')
require(set(atlas.support_scope.astype(str))=={'oracle_asserted'},'transition support scope drift')
require(set(atlas.readability_status.astype(str)).issuperset({'hidden','ambiguous','protocol_sensitive','identified'}),'resource status coverage')

market=json.load(open(ROOT/'results/market_strict_lattice_summary.json'))
require(market['source_full_lattice_rows']==3888,'market source lattice rows')
require(market['source_full_lattice_sha256']=='3a3cf4e1a2562d504ac96ab364c8ebce1b5170c805cf58042674ad6f27e6d49c','market lattice source hash')
require(market['strict_lattice_rows']==144,'strict lattice size')
require(market['strict_status_counts']=={'identified_readout':39,'not_identifiable':57,'ambiguous':48},'strict status counts')
require(market['strict_support_scope_values']==['not_asserted'],'market support scope drift')

boot=json.load(open(ROOT/'certificates/market_primary_gmm_bootstrap_certificate_v2_1.json'))
require(boot['status_counts']=={'primary_gmm_bootstrap_stable':5,'primary_gmm_bootstrap_protocol_sensitive':3},'bootstrap headline')
require(boot['support_scope']=='not_asserted','bootstrap support scope')
mn=json.load(open(ROOT/'certificates/market_multinull_primary_gmm_audit_v2_3.json'))
require(mn['restricted_lattice_protocols']==105,'multi-null lattice size')
require(mn['intersection_status_counts']=={'unadjusted_readout_only':57,'ambiguous':36,'not_identifiable':7,'null_family_sensitive':5},'multi-null intersection counts')
require(mn['intersection_status_counts'].get('multi_null_confirmed',0)==0,'multi-null overclaim')
focus=json.load(open(ROOT/'certificates/market_multinull_focus_audit_v2_4.json'))
require(focus['status_counts']=={'null_family_sensitive':9,'unadjusted_readout_only':3},'focus counts')
require(focus['support_scope']=='not_asserted','focus support scope')

src=json.load(open(ROOT/'SOURCE_DOCUMENTS.json'))
require(src['manuscript']['pdf_sha256']=='36f106a1ba6b2e8f524ca3b5d52aab6577596144a9117b6c01de1f6bb5a02ae9','manuscript hash drift')
require(src['manuscript']['distributed_in_public_v0_1'] is False,'manuscript distribution flag')
require(src['recovered_code']['baseline_detector_audit_v16.py']['public_release_status']=='curated_behaviorally_qualified_runner','synthetic runner provenance status')
require(src['recovered_code']['baseline_detector_audit_v16.py']['distributed_as_byte_identical_source'] is False,'synthetic runner byte-identity boundary')
require(all(v.get('distributed_in_public_v0_1') is False for k,v in src['recovered_code'].items() if k!='baseline_detector_audit_v16.py'),'market runner distribution flags')
require(src['frozen_tables']['readability_transition_alpha_sweep_v2_9.csv']['sha256']=='4f4860d1c52add16ec2ee7591df7fd1b1c2c4ff8f22566b1a5d5214e8c8e2d1e','transition source hash')
require(src['frozen_tables']['market_band_protocol_sweep.csv']['sha256']=='3a3cf4e1a2562d504ac96ab364c8ebce1b5170c805cf58042674ad6f27e6d49c','market source hash lock')
require(src['frozen_tables']['readability_transition_resource_query_atlas_v2_9.csv']['distributed_in_public_v0_1'] is False,'resource atlas distribution flag')

readme=(ROOT/'README.md').read_text(encoding='utf-8')
for phrase in ['A detector output is not a regime claim by itself.','support_scope = not_asserted','0 multi-null-confirmed','exact frozen `market_atlas_series.csv`','provenance-locks the full lattice','not represented as a byte-identical copy']:
    require(phrase in readme,'README missing boundary: '+phrase)

flags=summary['claim_flags']
require(all(v is False for v in flags.values()),'overclaim flag set true')
require(summary['market']['exact_frozen_market_rerun_self_contained'] is False,'market reproduction boundary drift')

manifest=json.load(open(ROOT/'MANIFEST.json'))
listed=set(manifest['files'])
actual=set()
for p in sorted(ROOT.rglob('*')):
    if p.is_file() and p.name!='MANIFEST.json' and 'outputs' not in p.relative_to(ROOT).parts:
        actual.add(p.relative_to(ROOT).as_posix())
require(actual==listed,'manifest file set mismatch')
print('PASS RRC public artifact validation')
