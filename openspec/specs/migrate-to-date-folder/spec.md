## ADDED Requirements

### Requirement: Migration script reads processed_papers.md to determine dates

The migration script SHALL parse `processed_papers.md` to build a mapping of paper filename to processing date. When the same paper appears under multiple date sections, the script SHALL use the last occurrence (most recent date).

#### Scenario: Paper appears once

- **WHEN** `paper1.pdf` appears under `## 2026-04-14` and nowhere else
- **THEN** the script SHALL assign date `2026-04-14` to `paper1.pdf`

#### Scenario: Paper appears multiple times (rerun history)

- **WHEN** `paper1.pdf` appears under `## 2026-04-14` and again under `## 2026-04-20`
- **THEN** the script SHALL assign date `2026-04-20` to `paper1.pdf`


<!-- @trace
source: add-date-folder-structure
updated: 2026-04-14
code:
  - tools/migrate.py
  - main.py
  - core/orchestrator.py
  - pa-start.bat
  - tools/init.py
-->

### Requirement: Migration moves files from old flat structure to date subfolders

For each paper in the date mapping, the script SHALL locate its existing output files in the old flat paths (`output/<cls>/pdf/`, `output/<cls>/json/`, `output/<cls>/summary/`) and move them to the corresponding date subfolder paths.

#### Scenario: Files found and moved successfully

- **WHEN** `paper1.pdf` is assigned date `2026-04-14` and exists at `output/A1/pdf/paper1.pdf`
- **THEN** the script SHALL create `output/A1/2026-04-14/pdf/` if it does not exist
- **THEN** the script SHALL move `paper1.pdf` to `output/A1/2026-04-14/pdf/paper1.pdf`
- **THEN** the corresponding `.md` and `.json` files SHALL also be moved to their respective date subfolders

#### Scenario: File not found in any classification folder

- **WHEN** a paper appears in `processed_papers.md` but no matching file exists in any old flat path
- **THEN** the script SHALL skip that paper and print a warning message
- **THEN** the script SHALL continue processing remaining papers


<!-- @trace
source: add-date-folder-structure
updated: 2026-04-14
code:
  - tools/migrate.py
  - main.py
  - core/orchestrator.py
  - pa-start.bat
  - tools/init.py
-->

### Requirement: Migration script reports summary and prompts cleanup

After completing all moves, the script SHALL print a summary of how many files were moved, skipped, and not found. The script SHALL then instruct the user to manually verify and delete the now-empty flat subdirectories (`pdf/`, `summary/`, `json/`) under each classification folder.

#### Scenario: Migration completes with mixed results

- **WHEN** the script finishes processing all entries
- **THEN** the script SHALL print the count of successfully moved files
- **THEN** the script SHALL print the count of skipped or not-found files
- **THEN** the script SHALL print instructions for manual cleanup of empty directories

## Requirements


<!-- @trace
source: add-date-folder-structure
updated: 2026-04-14
code:
  - tools/migrate.py
  - main.py
  - core/orchestrator.py
  - pa-start.bat
  - tools/init.py
-->

### Requirement: Migration script reads processed_papers.md to determine dates

The migration script SHALL parse `processed_papers.md` to build a mapping of paper filename to processing date. When the same paper appears under multiple date sections, the script SHALL use the last occurrence (most recent date).

#### Scenario: Paper appears once

- **WHEN** `paper1.pdf` appears under `## 2026-04-14` and nowhere else
- **THEN** the script SHALL assign date `2026-04-14` to `paper1.pdf`

#### Scenario: Paper appears multiple times (rerun history)

- **WHEN** `paper1.pdf` appears under `## 2026-04-14` and again under `## 2026-04-20`
- **THEN** the script SHALL assign date `2026-04-20` to `paper1.pdf`

---
### Requirement: Migration moves files from old flat structure to date subfolders

For each paper in the date mapping, the script SHALL locate its existing output files in the old flat paths (`output/<cls>/pdf/`, `output/<cls>/json/`, `output/<cls>/summary/`) and move them to the corresponding date subfolder paths.

#### Scenario: Files found and moved successfully

- **WHEN** `paper1.pdf` is assigned date `2026-04-14` and exists at `output/A1/pdf/paper1.pdf`
- **THEN** the script SHALL create `output/A1/2026-04-14/pdf/` if it does not exist
- **THEN** the script SHALL move `paper1.pdf` to `output/A1/2026-04-14/pdf/paper1.pdf`
- **THEN** the corresponding `.md` and `.json` files SHALL also be moved to their respective date subfolders

#### Scenario: File not found in any classification folder

- **WHEN** a paper appears in `processed_papers.md` but no matching file exists in any old flat path
- **THEN** the script SHALL skip that paper and print a warning message
- **THEN** the script SHALL continue processing remaining papers

---
### Requirement: Migration script reports summary and prompts cleanup

After completing all moves, the script SHALL print a summary of how many files were moved, skipped, and not found. The script SHALL then instruct the user to manually verify and delete the now-empty flat subdirectories (`pdf/`, `summary/`, `json/`) under each classification folder.

#### Scenario: Migration completes with mixed results

- **WHEN** the script finishes processing all entries
- **THEN** the script SHALL print the count of successfully moved files
- **THEN** the script SHALL print the count of skipped or not-found files
- **THEN** the script SHALL print instructions for manual cleanup of empty directories