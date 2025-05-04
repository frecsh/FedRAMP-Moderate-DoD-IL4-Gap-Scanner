"""Tests for the gap analyzer module."""

import json
import os
import tempfile

import pytest

from fedramp_il4_scanner.analyzer import GapAnalyzer


def test_gap_analyzer_initialization(sample_mapping_path):
    """Test gap analyzer initialization."""
    analyzer = GapAnalyzer(sample_mapping_path)
    assert analyzer is not None
    assert analyzer.mapping_path == sample_mapping_path
    assert analyzer.mapping_data is not None
    assert "mappings" in analyzer.mapping_data
    assert "metadata" in analyzer.mapping_data


def test_gap_analyzer_load_mapping_nonexistent():
    """Test loading a non-existent mapping file."""
    with pytest.raises(FileNotFoundError):
        GapAnalyzer("/nonexistent/mapping.json")


def test_gap_analyzer_load_mapping_invalid(temp_dir):
    """Test loading an invalid mapping file."""
    # Create an invalid mapping file
    invalid_file = os.path.join(temp_dir, "invalid.json")
    with open(invalid_file, 'w') as f:
        f.write("{ invalid json")
    
    with pytest.raises(ValueError):
        GapAnalyzer(invalid_file)


def test_analyze_gaps(analyzer):
    """Test gap analysis with implemented and missing controls."""
    # Sample controls from the SSP - only includes AC-1, not CM-6
    implemented_controls = [
        {
            "control-id": "AC-1",
            "statements": [{"statement-id": "AC-1.1", "description": "Test statement"}]
        }
    ]
    
    gaps = analyzer.analyze_gaps(implemented_controls)
    
    # We should have at least one gap (CM-6) based on our sample mapping
    assert len(gaps) > 0
    
    # Verify we found CM-6 as a gap
    cm6_found = False
    for gap in gaps:
        if gap["control-id"] == "CM-6":
            cm6_found = True
            assert "title" in gap
            assert "impact" in gap
            assert "effort" in gap
            assert "guidance" in gap
    
    assert cm6_found, "CM-6 gap not found"
    
    # Verify AC-1 is not in the gaps, since it's implemented
    ac1_found = False
    for gap in gaps:
        if gap["control-id"] == "AC-1":
            ac1_found = True
    
    assert not ac1_found, "AC-1 should not be in gaps since it's implemented"


def test_get_control_metrics(analyzer):
    """Test getting control metrics."""
    # Sample controls from the SSP - only implements AC-1, missing CM-6
    implemented_controls = [
        {
            "control-id": "AC-1",
            "statements": [{"statement-id": "AC-1.1", "description": "Test statement"}]
        }
    ]
    
    metrics = analyzer.get_control_metrics(implemented_controls)
    
    # Verify metrics structure
    assert "total_required" in metrics
    assert "total_implemented" in metrics
    assert "total_missing" in metrics
    assert "compliance_percentage" in metrics
    assert "missing_by_impact" in metrics
    
    # Verify some specific values
    assert metrics["total_implemented"] >= 1  # AC-1
    assert metrics["total_missing"] >= 1      # CM-6
    assert metrics["compliance_percentage"] > 0  # Some percentage
    assert metrics["compliance_percentage"] <= 100  # Maximum 100%
    
    # Missing by impact should have at least Medium (for CM-6)
    assert "Medium" in metrics["missing_by_impact"]
    assert metrics["missing_by_impact"]["Medium"] >= 1


def test_verify_mapping_integrity(analyzer):
    """Test mapping integrity verification."""
    # Valid mapping should pass integrity check
    assert analyzer.verify_mapping_integrity() is True


def test_verify_mapping_integrity_invalid(temp_dir):
    """Test mapping integrity verification with invalid mapping."""
    # Create an invalid mapping file missing required keys
    invalid_file = os.path.join(temp_dir, "invalid_mapping.json")
    with open(invalid_file, 'w') as f:
        json.dump({"some_key": "some_value"}, f)
    
    analyzer = GapAnalyzer(invalid_file)
    assert analyzer.verify_mapping_integrity() is False