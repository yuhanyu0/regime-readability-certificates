# Reproducibility status

## 1. Synthetic detector benchmark — executable and checked

The recovered historical source `baseline_detector_audit_v16.py` is provenance-locked in `SOURCE_DOCUMENTS.json`. Public v0.1 includes a curated executable release implementation as `experiments/baseline_detector_audit.py`.

The public runner is **not claimed to be byte-identical** to the recovered historical source. Its qualification criterion is behavioral: the regenerated five-world × four-detector decision table must match the frozen `baseline_detector_experiment_summary_v1_6.csv` on detector decisions and RRC fields.

Run:

```bash
pip install -r requirements.txt
python experiments/baseline_detector_audit.py
python scripts/check_synthetic_reproduction.py
```

The 50-seed v1.9 table is included as a frozen robustness result. Its GMM/HMM entries are proxy-style seed-sweep implementations and should not be conflated with the exact main benchmark implementations.

## 2. Controlled readability transition — compact public summary

The source experiment contains 620 alpha-sweep rows (31 alpha values × 20 seeds) and a 190-cell resource/query atlas. Public v0.1 includes:

- a 31-row across-seed alpha summary;
- a compact 190-cell resource/query status map;
- the v2.9 machine-readable certificate.

The full 620-row alpha table and full resource/query atlas are provenance-locked by SHA-256 in `SOURCE_DOCUMENTS.json` but are not duplicated in this curated release. The exact historical transition-generation script has not been identified as a standalone canonical file, so v0.1 does not present a newly written replacement runner as original code.

## 3. Market statistical audits — compact frozen summaries

Public v0.1 includes compact frozen summaries/certificates for the 3,888-protocol lattice, time-split transfer audit, primary-GMM bootstrap, and multi-null audits. The full 3,888-row lattice and the recovered market-analysis source scripts are provenance-locked by SHA-256 rather than duplicated here. Because the exact frozen derived market series is missing, shipping those runners without their canonical input would not make the market result self-contained.

The missing piece for a self-contained exact market rerun is the frozen rolling `market_atlas_series.csv`, or equivalently the exact cached `market_prices_auto.csv` used to construct it. References to those files exist in the archive, but the source file itself has not been recovered as a standalone canonical asset in the current library.

**v0.1 therefore does not download current prices and present the result as a reproduction of the frozen June 2026 run.** A later version may add the exact cached panel/derived atlas only after its provenance is verified.

## 4. Manuscript provenance

The v3.7 manuscript PDF and TeX source are provenance-locked by SHA-256 in `SOURCE_DOCUMENTS.json`. They are not duplicated in this curated GitHub v0.1; see `paper/README.md`.

## 5. Empirical transfer wording

The external-panel and panel-slice checks are portability/transfer audits over universe slices and controls. They are not independent external-data replication. All remain `support_scope = not_asserted`.
