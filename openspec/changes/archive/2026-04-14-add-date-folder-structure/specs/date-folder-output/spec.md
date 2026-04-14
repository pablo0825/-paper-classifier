## ADDED Requirements

### Requirement: Output path includes processing date

When saving a processed paper, the system SHALL write output files under a date subfolder named after the processing date (YYYY-MM-DD format), inserted between the classification folder and the type subfolder.

The output path structure SHALL be: `output/<classification>/<YYYY-MM-DD>/<type>/<filename>`

Where `<type>` is one of `pdf`, `summary`, or `json`.

#### Scenario: New paper saved on processing date

- **WHEN** a paper is successfully processed on 2026-04-14 and classified as A1
- **THEN** the PDF is moved to `output/A1/2026-04-14/pdf/<filename>.pdf`
- **THEN** the summary is written to `output/A1/2026-04-14/summary/<stem>.md`
- **THEN** the JSON is written to `output/A1/2026-04-14/json/<stem>.json`

#### Scenario: Date subfolder created automatically

- **WHEN** the date subfolder does not yet exist at save time
- **THEN** the system SHALL create it (and any parent directories) automatically

### Requirement: Summary rebuild scans across all date subfolders

When rebuilding the summary file for a classification (e.g., `summary_A1.md`), the system SHALL scan all date subfolders under that classification for JSON files.

#### Scenario: Papers from multiple dates appear in summary

- **WHEN** `output/A1/` contains `2026-04-14/json/paper1.json` and `2026-04-15/json/paper2.json`
- **THEN** `summary_A1.md` SHALL include entries for both paper1 and paper2

### Requirement: Rerun clears stale files from all date subfolders

When a paper is reprocessed (via rerun), the system SHALL remove any existing summary and JSON files for that paper from all other date subfolders under any classification folder.

#### Scenario: Rerun on a different day removes old date folder files

- **WHEN** `paper1.json` exists under `output/A1/2026-04-14/json/`
- **AND** the same paper is reprocessed on 2026-04-20 and still classified A1
- **THEN** `output/A1/2026-04-14/json/paper1.json` SHALL be deleted
- **THEN** the new result SHALL be written to `output/A1/2026-04-20/json/paper1.json`
