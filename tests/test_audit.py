"""Tests for the audit logging module."""

import os
import re
import time

import pytest

from fedramp_il4_scanner.audit import AuditLogger


def test_audit_logger_initialization(temp_log_path):
    """Test audit logger initialization."""
    logger = AuditLogger(temp_log_path)
    assert logger is not None
    assert logger.log_path == temp_log_path
    assert os.path.exists(temp_log_path)


def test_audit_logger_default_initialization(temp_dir):
    """Test audit logger initialization with default path."""
    # Save current home directory
    original_home = os.environ.get("HOME")
    
    try:
        # Temporarily set home directory to our temp dir
        os.environ["HOME"] = temp_dir
        
        logger = AuditLogger()
        assert logger is not None
        
        # Verify log file was created in expected location
        log_dir = os.path.join(temp_dir, ".fedramp_il4_scanner", "logs")
        assert os.path.isdir(log_dir)
        
        # The log file should be in the directory with a timestamped name
        log_files = [f for f in os.listdir(log_dir) if f.startswith("audit_")]
        assert len(log_files) > 0
        assert logger.log_path == os.path.join(log_dir, log_files[0])
    finally:
        # Restore original home directory
        if original_home:
            os.environ["HOME"] = original_home


def test_log_scan_start(audit_logger):
    """Test logging scan start."""
    audit_logger.log_scan_start("/path/to/ssp.json", "/path/to/mapping.json")
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Starting scan of /path/to/ssp.json" in log_content
    assert "with mapping /path/to/mapping.json" in log_content


def test_log_scan_complete(audit_logger):
    """Test logging scan complete."""
    audit_logger.log_scan_complete("/path/to/ssp.json", 10, 3)
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Scan complete for /path/to/ssp.json" in log_content
    assert "Analyzed 10 controls, identified 3 gaps" in log_content


def test_log_validation_result_success(audit_logger):
    """Test logging validation success."""
    audit_logger.log_validation_result("/path/to/ssp.json", True, {"message": "Success"})
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "OSCAL validation successful for ssp.json" in log_content


def test_log_validation_result_failure(audit_logger):
    """Test logging validation failure."""
    audit_logger.log_validation_result("/path/to/ssp.json", False, {"error": "Invalid format"})
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "OSCAL validation failed for ssp.json" in log_content
    assert "Invalid format" in log_content


def test_log_control_extraction(audit_logger):
    """Test logging control extraction."""
    audit_logger.log_control_extraction("/path/to/ssp.json", 15)
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Extracted 15 controls from ssp.json" in log_content


def test_log_gap_analysis(audit_logger):
    """Test logging gap analysis."""
    audit_logger.log_gap_analysis(3, ["AC-1", "CM-6", "IA-2"])
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Gap analysis complete: 3 gaps identified" in log_content
    # Check for debug log with missing controls
    assert "AC-1, CM-6, IA-2" in log_content


def test_log_report_generation(audit_logger):
    """Test logging report generation."""
    audit_logger.log_report_generation("/path/to/report.json")
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Report generated at /path/to/report.json" in log_content


def test_log_error(audit_logger):
    """Test logging errors."""
    try:
        # Generate an exception
        raise ValueError("Test error")
    except Exception as e:
        audit_logger.log_error("test operation", e)
    
    # Verify the log contains expected content
    with open(audit_logger.log_path, 'r') as f:
        log_content = f.read()
    
    assert "Error during test operation: Test error" in log_content


def test_get_log_path(audit_logger):
    """Test getting log path."""
    log_path = audit_logger.get_log_path()
    assert log_path == audit_logger.log_path
    assert os.path.exists(log_path)