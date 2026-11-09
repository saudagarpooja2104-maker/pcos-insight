# Structured PCOS Dataset Assessment

## Decision

Do not train or ship a PCOS risk model yet. The project needs a dataset with documented provenance, a license that clearly permits this academic use, appropriate clinical labels, and input fields that match the model's intended use. The commonly cited structured candidate needs a license clarification and does not directly match the current app's tracking data. An ultrasound image candidate is now documented below, but its public record does not state a license and its source provenance needs clarification, so it is not approved for model training or redistribution either.

## Candidate: Kottarathil PCOS dataset

The Kaggle dataset is widely used in PCOS classification research. Recent papers describe 541 women from 10 Indian hospitals, including 177 PCOS and 364 non-PCOS records, with clinical, laboratory, symptom, lifestyle, and ultrasound-derived features. One recent analysis says the clinical label was assigned by treating clinicians using the 2003 Rotterdam criteria, but was not independently re-verified in that retrospective dataset.

The license needs clarification before reuse. A 2025 systematic review lists the 541-record dataset as CC BY-NC-SA 4.0, while the current Kaggle contributor listing describes its files as `UNSPECIFIED`. Treat the current repository's terms as unresolved until the owner or institution confirms the applicable license and reuse conditions.

The available fields also differ from the inputs currently collected by PCOS Insight. The app records dates, user-described symptoms, severity, and optional lifestyle notes. The research dataset includes formal clinical, biochemical, and ultrasound measurements. Any study would need a documented subset and an explicit explanation of how its inputs correspond to app fields. If input features repeat components used to assign the PCOS label, the evaluation could measure agreement with those same criteria rather than independent screening performance.

## Candidate: Dryad cytokine dataset

A 2026 Dryad dataset is documented with de-identified data from 40 women (20 PCOS and 20 controls), matched for age, BMI, and race, with written consent for future research use. Its 96 immune-protein measurements are laboratory assay features, not fields collected by this application. Its small, matched sample and distinct feature set make it unsuitable for the planned user-entry risk estimate, though it may be relevant to a separate research question.

## Candidate: PCOSGen ultrasound images

The authors' Zenodo training record describes 3,200 healthy and unhealthy ultrasound instances annotated with help from an experienced gynaecologist. It also says the images were collected from multiple internet resources, including YouTube, ultrasoundcases.info, and Kaggle. The linked test record describes 1,468 images labeled for general normal/abnormal appearance and, for abnormal images, visibility of a polycystic ovary. Both records show an empty License field. Public availability and a research challenge description do not establish permission to reuse all underlying images; ask the dataset authors for license and source-rights clarification before downloading for model development, redistribution, or deployment.

Even if permission is clarified, these image labels and challenge data do not establish a clinically validated PCOS diagnosis model. The app's current ultrasound feature is private image intake and preview only; it has no classifier. Keep that boundary until provenance, patient-level splits, label definitions, and external clinical validation are addressed. This image dataset also cannot train the structured risk estimate, whose inputs are user-entered tracking data.

## Required checks before modeling

1. Obtain written confirmation of the dataset license and permitted academic reuse.
2. Record the source institution, collection method, cohort, inclusion criteria, label definition, and data dictionary.
3. Check for duplicates, identifiers, missing-value conventions, class balance, and overlap with diagnosis criteria.
4. Define the model's intended inputs in advance and exclude features unavailable to the app or that directly leak the target label.
5. Use patient-level separation for validation, compare the synopsis classifiers, and report sensitivity, specificity, precision, recall, F1, ROC-AUC, confusion matrices, and uncertainty. Do not claim clinical validation.
6. For image work, additionally confirm rights for the source images, inspect the dataset documentation and labels, and keep the image task separate from symptom/cycle risk estimation.

## Sources

- [Kaggle dataset page](https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos)
- [Systematic review of PCOS datasets and detection tools (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12032871/)
- [Recent PCOS dataset analysis (2026)](https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2026.1760541/full)
- [Dryad cytokine dataset and documentation (2026)](https://datadryad.org/dataset/doi:10.5061/dryad.ttdz08m9t)
- [PCOSGen-train dataset record (Zenodo)](https://zenodo.org/records/10430727)
- [PCOSGen-test dataset record (Zenodo, updated version)](https://zenodo.org/records/14591782)
