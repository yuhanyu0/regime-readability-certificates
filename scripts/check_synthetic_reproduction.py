from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
frozen=pd.read_csv(ROOT/'results/baseline_detector_experiment_summary_v1_6.csv').sort_values('world').reset_index(drop=True)
new_path=ROOT/'outputs/tables/baseline_detector_experiment_summary_v1_6.csv'
if not new_path.exists():
    raise SystemExit('Run: python experiments/baseline_detector_audit.py')
new=pd.read_csv(new_path).sort_values('world').reset_index(drop=True)
cols=['world','GMM','HMM','change_point','threshold','readability_status','support_scope','persistence_status','selection_status']
if not frozen[cols].astype(str).equals(new[cols].astype(str)):
    print('FROZEN')
    print(frozen[cols].to_string(index=False))
    print('REGENERATED')
    print(new[cols].to_string(index=False))
    raise SystemExit('Synthetic reproduction mismatch')
print('PASS synthetic detector audit: regenerated decisions and RRC fields match frozen v1.6')
