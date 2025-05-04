"""Integration tests for FedRAMP IL4 Scanner.

These tests verify the end-to-end functionality by running the actual
scanner against real files without mocking dependencies.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fedramp_il4_scanner.scanner import IL4Scanner


@pytest.fixture
def sample_oscal_ssp_file(temp_dir):
    """Create a realistic sample OSCAL SSP file."""
    ssp_file = os.path.join(temp_dir, "sample_ssp.json")
    
    # Create a minimal but valid OSCAL SSP file
    ssp_data = {
        "oscal-version": "1.0.0",
        "system-security-plan": {
            "uuid": "00000000-0000-4000-8000-000000000000",
            "metadata": {
                "title": "Integration Test SSP",
                "version": "1.0",
                "last-modified": "2023-01-01T00:00:00Z",
                "oscal-version": "1.0.0",
                "parties": [
                    {
                        "uuid": "00000000-0000-4000-8000-000000000001",
                        "type": "organization",
                        "name": "Test Organization"
                    }
                ]
            },
            "system-characteristics": {
                "system-name": "Test System",
                "system-id": {
                    "identifier-type": "https://fedramp.gov",
                    "id": "TEST-SYSTEM-ID"
                },
                "description": "Test system for integration testing",
                "security-sensitivity-level": "moderate",
                "system-information": {
                    "information-types": [
                        {
                            "uuid": "00000000-0000-4000-8000-000000000002",
                            "title": "Test Information",
                            "description": "Test information type",
                            "categorizations": [
                                {
                                    "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                                    "information-type-ids": ["test-id"]
                                }
                            ],
                            "confidentiality-impact": {"base": "moderate"},
                            "integrity-impact": {"base": "moderate"},
                            "availability-impact": {"base": "moderate"}
                        }
                    ]
                },
                "security-impact-level": {
                    "security-objective-confidentiality": "moderate",
                    "security-objective-integrity": "moderate",
                    "security-objective-availability": "moderate"
                },
                "status": {
                    "state": "operational"
                },
                "authorization-boundary": {
                    "description": "Test authorization boundary"
                }
            },
            "system-implementation": {
                "users": [
                    {
                        "uuid": "00000000-0000-4000-8000-000000000003",
                        "role-ids": ["admin"],
                        "authorized-privileges": [
                            {
                                "title": "Test Privilege",
                                "description": "Test privilege description"
                            }
                        ]
                    }
                ],
                "components": [
                    {
                        "uuid": "00000000-0000-4000-8000-000000000004",
                        "type": "software",
                        "title": "Test Component",
                        "description": "Test component description",
                        "status": {
                            "state": "operational"
                        }
                    }
                ]
            },
            "control-implementation": {
                "description": "Test control implementation",
                "implemented-requirements": [
                    {
                        "uuid": "00000000-0000-4000-8000-000000000005",
                        "control-id": "AC-1",
                        "description": "Test access control policy",
                        "statements": [
                            {
                                "uuid": "00000000-0000-4000-8000-000000000006",
                                "statement-id": "AC-1.a",
                                "description": "The organization develops and documents access control policy and procedures."
                            }
                        ]
                    },
                    {
                        "uuid": "00000000-0000-4000-8000-000000000007",
                        "control-id": "AU-2",
                        "description": "Test audit events",
                        "statements": [
                            {
                                "uuid": "00000000-0000-4000-8000-000000000008",
                                "statement-id": "AU-2.a",
                                "description": "The organization determines the types of events to audit."
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    with open(ssp_file, 'w') as f:
        json.dump(ssp_data, f, indent=2)
    
    return ssp_file


@pytest.mark.integration
def test_end_to_end_scan(sample_oscal_ssp_file, sample_mapping_path, temp_dir):
    """Test a full end-to-end scan without mocks."""
    # Create output directory
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the scanner
    scanner = IL4Scanner()
    result = scanner.scan(sample_oscal_ssp_file, sample_mapping_path, output_dir)
    
    # Basic assertions
    assert result["status"] == "success"
    assert result["ssp_file"] == sample_oscal_ssp_file
    assert result["mapping_file"] == sample_mapping_path
    assert result["controls_analyzed"] >= 2  # At least AC-1 and AU-2
    assert result["gaps_identified"] > 0     # Should identify gaps
    assert result["compliance_percentage"] >= 0.0
    assert result["compliance_percentage"] <= 100.0
    
    # Check output files
    report_path = os.path.join(output_dir, "gap_raw.json")
    assert os.path.exists(report_path)
    
    # Verify report content
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    assert "gaps" in report_data
    assert "metrics" in report_data
    assert report_data["metrics"]["total_required"] > 0
    assert report_data["metrics"]["total_implemented"] >= 0
    assert report_data["metrics"]["total_missing"] > 0


@pytest.mark.integration
def test_cli_execution(sample_oscal_ssp_file, sample_mapping_path, temp_dir):
    """Test executing the CLI directly as a subprocess."""
    # Create output directory
    output_dir = os.path.join(temp_dir, "cli_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the path to the CLI script
    cli_module = Path(__file__).parent.parent / "fedramp_il4_scanner" / "cli.py"
    
    # Execute the CLI command
    command = [
        sys.executable, str(cli_module), "scan",
        sample_oscal_ssp_file,
        "--mapping", sample_mapping_path,
        "--output", output_dir
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Check the CLI output
    assert result.returncode == 0
    assert "Scan Complete" in result.stdout
    assert "Controls Analyzed" in result.stdout
    assert "Gaps Identified" in result.stdout
    assert "Compliance Percentage" in result.stdout
    
    # Verify output files were created
    files = os.listdir(output_dir)
    assert any(file.startswith("gap_raw") for file in files)


@pytest.mark.integration
def test_mapping_verification_cli(sample_mapping_path):
    """Test the mapping verification command through CLI."""
    # Get the path to the CLI script
    cli_module = Path(__file__).parent.parent / "fedramp_il4_scanner" / "cli.py"
    
    # Execute the verify-mapping command
    command = [
        sys.executable, str(cli_module), "verify-mapping",
        sample_mapping_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Check the CLI output
    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert "passed integrity checks" in result.stdout