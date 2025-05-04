"""Tests for the main scanner module."""

import json
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fedramp_il4_scanner.audit import AuditLogger
from fedramp_il4_scanner.scanner import IL4Scanner


@pytest.fixture
def temp_output_dir(temp_dir):
    """Create a temporary output directory for scan results."""
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def test_scanner_initialization(audit_logger):
    """Test scanner initialization."""
    scanner = IL4Scanner(audit_logger)
    assert scanner is not None
    assert scanner.audit_logger == audit_logger
    assert scanner.validator is not None
    assert scanner.storage is not None


def test_scanner_default_initialization():
    """Test scanner initialization with default audit logger."""
    scanner = IL4Scanner()
    assert scanner is not None
    assert scanner.audit_logger is not None
    assert scanner.validator is not None
    assert scanner.storage is not None


@patch('fedramp_il4_scanner.validation.OscalValidator.validate_file')
@patch('fedramp_il4_scanner.validation.OscalValidator.get_ssp_metadata')
@patch('fedramp_il4_scanner.validation.OscalValidator.extract_controls')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.verify_mapping_integrity')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.analyze_gaps')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.get_control_metrics')
@patch('fedramp_il4_scanner.storage.ScanStorage.store_ssp_metadata')
@patch('fedramp_il4_scanner.storage.ScanStorage.store_controls')
@patch('fedramp_il4_scanner.storage.ScanStorage.store_gaps')
def test_scan_success(mock_store_gaps, mock_store_controls, mock_store_ssp, 
                     mock_get_metrics, mock_analyze_gaps, mock_verify_mapping,
                     mock_extract_controls, mock_get_metadata, mock_validate,
                     sample_ssp_path, sample_mapping_path, temp_output_dir, audit_logger):
    """Test the full scan process with mocked dependencies."""
    
    # Set up mock returns
    mock_validate.return_value = (True, {"message": "Success"})
    mock_get_metadata.return_value = {"title": "Test SSP", "version": "1.0"}
    mock_extract_controls.return_value = [
        {"control-id": "AC-1", "statements": [{"statement-id": "AC-1.1", "description": "Test"}]}
    ]
    mock_verify_mapping.return_value = True
    mock_analyze_gaps.return_value = [
        {"control-id": "CM-6", "title": "Configuration Settings"}
    ]
    mock_get_metrics.return_value = {
        "total_required": 2,
        "total_implemented": 1,
        "total_missing": 1,
        "compliance_percentage": 50.0,
        "missing_by_impact": {"Medium": 1}
    }
    mock_store_ssp.return_value = 1  # scan_id
    mock_store_controls.return_value = [1]  # control_ids
    mock_store_gaps.return_value = [1]  # gap_ids
    
    # Create scanner and run scan
    scanner = IL4Scanner(audit_logger)
    result = scanner.scan(sample_ssp_path, sample_mapping_path, temp_output_dir)
    
    # Verify all methods were called
    mock_validate.assert_called_once_with(sample_ssp_path)
    mock_get_metadata.assert_called_once_with(sample_ssp_path)
    mock_extract_controls.assert_called_once_with(sample_ssp_path)
    mock_verify_mapping.assert_called_once()
    mock_analyze_gaps.assert_called_once()
    mock_get_metrics.assert_called_once()
    mock_store_ssp.assert_called_once()
    mock_store_controls.assert_called_once()
    mock_store_gaps.assert_called_once()
    
    # Verify scan result structure
    assert result is not None
    assert result["status"] == "success"
    assert result["scan_id"] == 1
    assert result["ssp_file"] == sample_ssp_path
    assert result["mapping_file"] == sample_mapping_path
    assert result["controls_analyzed"] == 1
    assert result["gaps_identified"] == 1
    assert result["compliance_percentage"] == 50.0
    assert "elapsed_time" in result
    assert "report_path" in result
    
    # Verify output file was created
    output_file = os.path.join(temp_output_dir, "gap_raw.json")
    assert os.path.exists(output_file)


@patch('fedramp_il4_scanner.validation.OscalValidator.validate_file')
def test_scan_validation_failure(mock_validate, sample_ssp_path, sample_mapping_path, temp_output_dir, audit_logger):
    """Test scan process with validation failure."""
    
    # Mock validation to fail
    mock_validate.return_value = (False, {"error": "Invalid SSP"})
    
    # Create scanner
    scanner = IL4Scanner(audit_logger)
    
    # Scan should raise ValueError due to validation failure
    with pytest.raises(ValueError) as excinfo:
        scanner.scan(sample_ssp_path, sample_mapping_path, temp_output_dir)
    
    assert "Invalid OSCAL SSP" in str(excinfo.value)
    mock_validate.assert_called_once_with(sample_ssp_path)


@patch('fedramp_il4_scanner.validation.OscalValidator.validate_file')
@patch('fedramp_il4_scanner.validation.OscalValidator.get_ssp_metadata')
@patch('fedramp_il4_scanner.validation.OscalValidator.extract_controls')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.verify_mapping_integrity')
def test_scan_mapping_integrity_failure(mock_verify_mapping, mock_extract_controls, 
                                       mock_get_metadata, mock_validate,
                                       sample_ssp_path, sample_mapping_path, 
                                       temp_output_dir, audit_logger):
    """Test scan process with mapping integrity failure."""
    
    # Set up mock returns
    mock_validate.return_value = (True, {"message": "Success"})
    mock_get_metadata.return_value = {"title": "Test SSP", "version": "1.0"}
    mock_extract_controls.return_value = [{"control-id": "AC-1"}]
    mock_verify_mapping.return_value = False  # Mapping integrity check fails
    
    # Create scanner
    scanner = IL4Scanner(audit_logger)
    
    # Scan should raise ValueError due to mapping integrity failure
    with pytest.raises(ValueError) as excinfo:
        scanner.scan(sample_ssp_path, sample_mapping_path, temp_output_dir)
    
    assert "Mapping file integrity check failed" in str(excinfo.value)
    mock_validate.assert_called_once_with(sample_ssp_path)
    mock_verify_mapping.assert_called_once()


def test_export_gap_json(temp_dir):
    """Test exporting gap data to JSON."""
    # Create scanner
    scanner = IL4Scanner()
    
    # Sample data
    gaps = [
        {"control-id": "CM-6", "title": "Configuration Settings", "impact": "Medium"}
    ]
    metrics = {
        "total_required": 2,
        "total_implemented": 1,
        "total_missing": 1,
        "compliance_percentage": 50.0
    }
    
    # Export data
    output_path = os.path.join(temp_dir, "test_gaps.json")
    result_path = scanner._export_gap_json(gaps, metrics, output_path)
    
    # Verify the file was created
    assert os.path.exists(result_path)
    assert result_path == output_path
    
    # Verify file contents
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    assert "gaps" in data
    assert "metrics" in data
    assert "generated_at" in data
    assert "version" in data
    assert data["gaps"] == gaps
    assert data["metrics"] == metrics


@patch('fedramp_il4_scanner.validation.OscalValidator.validate_file')
@patch('fedramp_il4_scanner.validation.OscalValidator.get_ssp_metadata')
@patch('fedramp_il4_scanner.validation.OscalValidator.extract_controls')
@patch('fedramp_il4_scanner.storage.ScanStorage.store_ssp_metadata')
def test_scan_recovers_from_control_extraction_error(mock_store_ssp, mock_extract_controls, 
                                                    mock_get_metadata, mock_validate,
                                                    sample_ssp_path, sample_mapping_path, 
                                                    temp_output_dir, audit_logger):
    """Test scan recovery when control extraction fails."""
    # Set up mock returns
    mock_validate.return_value = (True, {"message": "Success"})
    mock_get_metadata.return_value = {"title": "Test SSP", "version": "1.0"}
    mock_store_ssp.return_value = 1  # scan_id
    
    # Mock control extraction to raise an exception
    mock_extract_controls.side_effect = Exception("Control extraction failed")
    
    # Create scanner
    scanner = IL4Scanner(audit_logger)
    
    # Scan should raise the exception, but audit logger should capture it
    with pytest.raises(Exception) as excinfo:
        scanner.scan(sample_ssp_path, sample_mapping_path, temp_output_dir)
    
    assert "Control extraction failed" in str(excinfo.value)
    
    # Verify audit logger was called to log the error
    # This is indirect testing since we can't easily mock the audit_logger.log_error method
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
        assert "Error during scan" in log_content
        assert "Control extraction failed" in log_content


def test_resilience_to_corrupt_input(temp_dir):
    """Test scanner resilience when handling corrupt input files."""
    # Create a corrupt JSON file
    corrupt_file = os.path.join(temp_dir, "corrupt.json")
    with open(corrupt_file, 'w') as f:
        f.write("{This is not valid JSON")
    
    # Create a valid mapping file
    mapping_file = os.path.join(temp_dir, "mapping.json")
    with open(mapping_file, 'w') as f:
        json.dump({
            "metadata": {"version": "1.0"},
            "mappings": {"AC-1": {"title": "Test", "required_for_il4": True}}
        }, f)
    
    # Create scanner
    scanner = IL4Scanner()
    
    # Scan should raise a ValueError but not crash
    with pytest.raises(ValueError) as excinfo:
        scanner.scan(corrupt_file, mapping_file, temp_dir)
    
    # The error should mention invalid JSON
    assert "Invalid" in str(excinfo.value)


@pytest.mark.parametrize("error_location", [
    "validate_file",
    "get_ssp_metadata", 
    "extract_controls",
    "verify_mapping_integrity",
    "analyze_gaps"
])
def test_error_handling_at_different_stages(error_location, sample_ssp_path, 
                                           sample_mapping_path, temp_output_dir):
    """Test error handling at different stages of the scanning process."""
    # First, set up the default mocks for all stages that should NOT fail
    with patch('fedramp_il4_scanner.validation.OscalValidator.validate_file',
               return_value=(True, {"message": "Success"})) as mock_validate, \
         patch('fedramp_il4_scanner.validation.OscalValidator.get_ssp_metadata',
               return_value={"title": "Test"}) as mock_get_metadata, \
         patch('fedramp_il4_scanner.validation.OscalValidator.extract_controls',
               return_value=[{"control-id": "AC-1"}]) as mock_extract_controls, \
         patch('fedramp_il4_scanner.analyzer.GapAnalyzer.verify_mapping_integrity',
               return_value=True) as mock_verify_mapping, \
         patch('fedramp_il4_scanner.analyzer.GapAnalyzer.analyze_gaps',
               return_value=[]) as mock_analyze_gaps, \
         patch('fedramp_il4_scanner.analyzer.GapAnalyzer.get_control_metrics',
               return_value={"compliance_percentage": 0}), \
         patch('fedramp_il4_scanner.storage.ScanStorage.store_ssp_metadata',
               return_value=1), \
         patch('fedramp_il4_scanner.storage.ScanStorage.store_controls'), \
         patch('fedramp_il4_scanner.storage.ScanStorage.store_gaps'):
        
        # Now set up the specific mock that SHOULD fail
        if error_location == "validate_file":
            mock_validate.return_value = (False, {"error": "Validation error"})
        elif error_location == "get_ssp_metadata":
            mock_get_metadata.side_effect = ValueError("Metadata error")
        elif error_location == "extract_controls":
            mock_extract_controls.side_effect = ValueError("Control error")
        elif error_location == "verify_mapping_integrity":
            mock_verify_mapping.return_value = False
        elif error_location == "analyze_gaps":
            mock_analyze_gaps.side_effect = ValueError("Analysis error")
        
        scanner = IL4Scanner()
        
        # Expect the scan to raise an exception with the appropriate message
        with pytest.raises(ValueError) as excinfo:
            scanner.scan(sample_ssp_path, sample_mapping_path, temp_output_dir)
        
        # Expected messages based on error location
        expected_messages = {
            "validate_file": "Invalid OSCAL SSP",
            "get_ssp_metadata": "Metadata error",
            "extract_controls": "Control error",
            "verify_mapping_integrity": "Mapping file integrity check failed",
            "analyze_gaps": "Analysis error"
        }
        
        assert expected_messages[error_location] in str(excinfo.value)