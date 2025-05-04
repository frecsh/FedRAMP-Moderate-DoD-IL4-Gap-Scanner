# 🛡️ FedRAMP Moderate → DoD IL4 Gap Scanner

## Local‑Only Implementation Plan (v 0.3)

---

### 🎯 Project Objective

Build a **single‑user, entirely local CLI tool** that ingests a FedRAMP Moderate OSCAL SSP, applies an authoritative FedRAMP→IL4 control‑mapping, and emits actionable gap reports (Markdown / CSV) plus an evidence manifest.

---

### 📊 Executive Summary

| Problem          | Manual reconciliation takes \~80 hrs per SSP                                        |
| ---------------- | ----------------------------------------------------------------------------------- |
| Solution         | Local scanner parses, matches, and reports in <2 min                                |
| Impact           | 50 %+ time reduction; traceable artifacts for ATO                                   |
| Scope Guardrails | **No** network calls, auth systems, eMASS, or multi‑user RBAC—CLI‐first, file‑based |


---

## 🔄 Phase 1 — Governance & Authoritative Mapping

### ✅ Objectives
- Establish authoritative control mappings between FedRAMP Moderate and DoD IL4
- Create versioned mapping JSON as the single source of truth
- Document interpretation methodology and assumptions

### 📋 Tasks
- [ ] Collect FedRAMP Mod & DoD IL4 deltas (ALL control families)
- [ ] Add CMMC 2.0 Level 2 mappings for comprehensive coverage
- [ ] Validate with public FedRAMP PMO docs or SME consult
- [ ] Record assumptions in *mapping‑methodology.md*
- [ ] Implement risk register for technical & implementation risks
- [ ] Calculate SHA-256 checksums for mapping files to prevent tampering
- [ ] Create version control strategy for tracking control interpretation changes

### 🔑 Deliverables
- `mappings.json` with SHA-256 checksums (control\_id → status/notes)
- `mapping‑methodology.md` (assumptions, sources)
- `risk-register.md` (identified risks and mitigations)
- Version controlled mapping repository with change history

---

## 🔧 Phase 2 — Core CLI & Parsing Foundation

### ✅ Objectives
- Create a local command line tool that parses OSCAL SSPs efficiently
- Implement secure local storage for parsed data
- Establish foundation for validation and comparison logic

### 📋 Tasks
- [x] Set up repo (`poetry` or `pipenv`) and secure coding linting
- [x] Implement pytest suite for test-driven development
- [x] Integrate `oscal‑py` + `nist-oscal` for redundant validation
- [x] Use TinyDB for lightweight local storage instead of raw JSON
- [x] Create CLI skeleton with Typer + wizard mode (`scan --ssp my_ssp.json --mapping mappings.json`)
- [x] Extract implemented control IDs & statements
- [x] Compare against mapping, mark *Implemented / Missing / Not Applicable*
- [x] Implement comprehensive audit logging of all actions
- [x] Support both OSCAL 1.0.0 and 1.1.0 formats

### 🔑 Deliverables
- [x] `scanner/cli.py` with command line interface
- [x] `scanner/storage.py` (TinyDB implementation)
- [x] `scanner/validation.py` for OSCAL validation
- [x] `sample_ssp/` test fixtures for validation
- [x] `gap_raw.json` output format
- [x] `scanner/audit.py` (logging implementation)

---

## ⚙️ Phase 3 — Control Assessment & Evidence Bundle

### ✅ Objectives
- Implement rule-based evaluation of control implementations
- Create secure evidence collection and verification framework
- Build confidence scoring for implementation quality assessment

### 📋 Tasks
- [ ] Pick top 10 IL4 delta controls and author Rego rules (run OPA via subprocess or WASM)
- [ ] Design minimal evidence schema (YAML/JSON) with fields: `id, control_ids, type, hash, timestamp`
- [ ] Implement `evidence/` folder ingestion and hash verification
- [ ] Compute confidence score = rule\_pass + evidence\_present
- [ ] Implement encrypted storage for sensitive mapping data (Fernet)
- [ ] Add progress indicators with estimated completion times
- [ ] Create integrity verification for evidence artifacts
- [ ] Design secure local storage with encryption at rest

### 🔑 Deliverables
- `rules/` directory with `.rego` files for policy evaluation
- `evidence_schema.json` defining required evidence structure
- `scanner/encryption.py` implementing secure storage
- Updated `gap_enriched.json` with confidence field
- `scanner/progress.py` for user feedback during processing
- Evidence integrity verification system

---

## 📊 Phase 4 — Reporting & Remediation Outputs

### ✅ Objectives
- Generate actionable, human-readable gap reports
- Provide remediation guidance and effort estimation
- Create templates for standard compliance documentation

### 📋 Tasks
- [ ] Implement Markdown & CSV report generator with templating options
- [ ] Embed remediation stubs sourced from NIST 800‑53 guidance
- [ ] Add T‑shirt effort estimate (S/M/L/XL) per gap
- [ ] Implement risk-based prioritization of gaps beyond effort estimation
- [ ] Create snapshot comparison to track progress between scans
- [ ] Build Control Implementation Statement Generator for missing controls
- [ ] Develop Evidence Collection Guidance with templates per control family
- [ ] Generate prioritized remediation roadmap based on impact

### 🔑 Deliverables
- `report.md`, `report.csv` with gap analysis and remediation guidance
- `poam_template.csv` for Plan of Actions & Milestones
- `scanner/templates/` directory with customizable report templates
- `scanner/comparator.py` for tracking compliance progress
- `evidence-templates/` with family-specific collection guidance
- Prioritized remediation planning output

---

## 🖥️ Phase 5 — Optional Local Visualization (Stretch)

### ✅ Objectives
- Create local data visualization for compliance status
- Enable drill-down analysis of compliance gaps
- Provide intuitive dashboard for tracking remediation progress

### 📋 Tasks
- [ ] Create low‑fi wireframe → simple bar chart by control family
- [ ] Implement control drill‑down page with evidence links
- [ ] Add SSP version tracking and comparison visualization
- [ ] Build local dashboard using Streamlit running on `localhost:8501`
- [ ] Create visual risk heatmap of compliance status
- [ ] Implement filtering and sorting capabilities for gap analysis

### 🔑 Deliverables
- `dashboard/app.py` (Streamlit implementation)
- `dashboard/comparison.py` for visual diff analysis
- Interactive compliance visualization
- Control family heatmap
- Drill-down analysis views

---

## 🗓️ Consolidated Timeline & Checkpoints

| Week | Milestone                                              |
| ---- | ------------------------------------------------------ |
| 1    | Repo scaffold, mapping JSON drafted, pytest framework  |
| 2    | CLI parses SSP & prints control list                   |
| 3    | Gap comparison logic + encryption layer complete       |
| 4    | First Rego rules + evidence schema                     |
| 5    | Confidence scoring + enriched JSON                     |
| 6    | Markdown/CSV report generator ready                    |
| 7    | Templates, prioritization, and comparison features     |
| 8    | SSP validation with real-world examples                |
| 9    | ☑ MVP freeze; optional Streamlit UI                    |

---

## 🚦 Success Metrics (Local‑MVP)

* ⏱️ **Runtime:** <120 s per 20 MB SSP
* ✅ **Accuracy:** ≥95 % gap detection on sample set
* 📄 **Report Quality:** Passes SME spot‑check with ≤5 minor edits
* 🔒 **Security:** 100% validation of mapping file integrity

---

## 🛑 Risk Management

| Risk | Mitigation |
|------|------------|
| Accuracy of mapping | Expert validation, comparison with authoritative sources |
| False positives/negatives | Test suite with known SSPs, confidence scoring |
| Tool security concerns | Encrypted storage, integrity verification, audit logging |
| OSCAL spec evolution | Version compatibility layer, support for multiple formats |
| Resource constraints | Prioritized MVP approach, local-only processing |
| User adoption | Intuitive CLI wizard, comprehensive documentation |

---

## ➡️ Future Extensions (Roadmap)

* Add cron/launchd wrapper for scheduled re‑scans
* Swap SQLite backend for multi‑user mode
* eMASS API adapter & POA\&M auto‑upload
* Cloud provider evidence collectors
* Integration with vulnerability scanners for control validation
* Digital Twin simulation for compliance outcomes
* Cross-CSP compliance unified view

---

### Notes

* Tested on macOS Monterey, Python 3.11, 16 GB RAM.
* All dependencies open‑source; air‑gap installs supported via `./vendor` directory.
* OSCAL compatibility with both 1.0.0 and 1.1.0.
