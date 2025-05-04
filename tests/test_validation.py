"""Tests for the OSCAL validation module."""

import json
import os
from pathlib import Path

import pytest

from fedramp_il4_scanner.validation import OscalValidator


def test_validator_initialization():
    """Test validator initialization."""
    validator = OscalValidator()
    assert validator is not None
    assert validator.valid_versions == ["1.0.0", "1.1.0"]


def test_validate_file_success(sample_ssp_path):
    """Test successful validation of a valid OSCAL file."""
    validator = OscalValidator()
    valid, details = validator.validate_file(sample_ssp_path)
    assert valid is True
    assert "message" in details
    assert details["message"] == "SSP validation successful"


def test_validate_file_nonexistent():
    """Test validation of a non-existent file."""
    validator = OscalValidator()
    valid, details = validator.validate_file("/nonexistent/file.json")
    assert valid is False
    assert "error" in details
    assert "File not found" in details["error"]


def test_validate_file_invalid_content(temp_dir):
    """Test validation with invalid content."""
    # Create an invalid file with non-OSCAL content
    invalid_file = os.path.join(temp_dir, "invalid.json")
    with open(invalid_file, 'w') as f:
        json.dump({"key": "value"}, f)
    
    validator = OscalValidator()
    valid, details = validator.validate_file(invalid_file)
    assert valid is False
    assert "error" in details
    assert "Not a valid OSCAL SSP document" in details["error"]


def test_extract_controls(sample_ssp_path):
    """Test control extraction from an OSCAL SSP."""
    validator = OscalValidator()
    controls = validator.extract_controls(sample_ssp_path)
    
    # We should have at least the controls defined in our sample SSP
    assert len(controls) >= 2
    
    # Check that AC-1 is in the controls
    ac1_found = False
    for control in controls:
        if control["control-id"] == "AC-1":
            ac1_found = True
            assert "statements" in control
            assert len(control["statements"]) > 0
            assert "statement-id" in control["statements"][0]
            assert control["statements"][0]["statement-id"] == "AC-1.1"
    
    assert ac1_found, "AC-1 control not found in extracted controls"


def test_get_ssp_metadata(sample_ssp_path):
    """Test metadata extraction from an OSCAL SSP."""
    validator = OscalValidator()
    metadata = validator.get_ssp_metadata(sample_ssp_path)
    
    # Check essential metadata fields
    assert "title" in metadata
    assert metadata["title"] == "Test SSP"
    assert "version" in metadata
    assert metadata["version"] == "1.0"
    assert "last-modified" in metadata
    assert "system-name" in metadata
    assert metadata["system-name"] == "Test System"


@pytest.mark.parametrize("oscal_version", [
    "1.0.0",      # Standard supported version
    "1.1.0",      # Standard supported version
    "0.9.0",      # Outdated version
    "2.0.0",      # Future version
    "invalid",    # Invalid version string
    None          # Missing version
])
def test_validation_with_different_versions(oscal_version, temp_dir):
    """Test validation with different OSCAL versions."""
    # Create a test SSP file with the specified version
    test_file = os.path.join(temp_dir, f"test_ssp_{oscal_version}.json")
    
    ssp_data = {
        "system-security-plan": {
            "metadata": {
                "title": "Test SSP",
                "version": "1.0"
            }
        }
    }
    
    # Add oscal-version if not None
    if oscal_version is not None:
        ssp_data["oscal-version"] = oscal_version
        
    with open(test_file, 'w') as f:
        json.dump(ssp_data, f)
    
    validator = OscalValidator()
    valid, details = validator.validate_file(test_file)
    
    # Only 1.0.0 and 1.1.0 should be fully supported
    if oscal_version in ["1.0.0", "1.1.0"]:
        # These might still fail validation due to incomplete content,
        # but should not fail just because of the version
        if not valid:
            assert "version" not in details.get("error", "").lower()
    

@pytest.mark.parametrize("control_data", [
    # Standard controls
    [
        {"control-id": "AC-1", "statements": [{"statement-id": "AC-1.1"}]},
        {"control-id": "AU-2", "statements": [{"statement-id": "AU-2.1"}]}
    ],
    # Empty controls list
    [],
    # Control with no statements
    [{"control-id": "AC-1", "statements": []}],
    # Control with unusual ID format
    [{"control-id": "CUSTOM-CONTROL-123", "statements": [{"statement-id": "a.b.c"}]}],
    # Very large number of controls (simulated)
    [{"control-id": f"AC-{i}", "statements": [{"statement-id": f"AC-{i}.1"}]} for i in range(1, 5)]
])
def test_extract_controls_variations(control_data, temp_dir):
    """Test extracting controls with various structures."""
    # Create a test SSP with the specified controls
    test_file = os.path.join(temp_dir, "test_controls.json")
    
    # Create a basic SSP structure
    ssp_data = {
        "oscal-version": "1.0.0",
        "system-security-plan": {
            "metadata": {
                "title": "Test SSP",
                "version": "1.0"
            },
            "control-implementation": {
                "implemented-requirements": control_data
            }
        }
    }
    
    with open(test_file, 'w') as f:
        json.dump(ssp_data, f)
    
    validator = OscalValidator()
    extracted_controls = validator.extract_controls(test_file)
    
    # Verify the number of extracted controls matches input
    assert len(extracted_controls) == len(control_data)
    
    # For non-empty input, verify control IDs match
    if control_data:
        input_control_ids = {ctrl["control-id"] for ctrl in control_data}
        extracted_control_ids = {ctrl["control-id"] for ctrl in extracted_controls}
        assert input_control_ids == extracted_control_ids