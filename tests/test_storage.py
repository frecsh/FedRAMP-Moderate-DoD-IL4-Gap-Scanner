"""Tests for the storage module."""

import json
import os
from pathlib import Path

import pytest
from tinydb import TinyDB

from fedramp_il4_scanner.storage import ScanStorage


def test_storage_initialization(temp_db_path):
    """Test storage initialization."""
    storage = ScanStorage(temp_db_path)
    assert storage is not None
    assert storage.db is not None
    assert storage.scans is not None
    assert storage.controls is not None
    assert storage.gaps is not None
    
    # Verify the file is created
    assert os.path.exists(temp_db_path)


def test_storage_default_initialization(temp_dir):
    """Test storage initialization with default path."""
    # Save current home directory
    original_home = os.environ.get("HOME")
    
    try:
        # Temporarily set home directory to our temp dir
        os.environ["HOME"] = temp_dir
        
        storage = ScanStorage()
        assert storage is not None
        
        # Verify the database was created in the default location
        expected_db_path = os.path.join(temp_dir, ".fedramp_il4_scanner", "scan_data.json")
        assert os.path.exists(expected_db_path)
    finally:
        # Restore original home directory
        if original_home:
            os.environ["HOME"] = original_home


def test_store_ssp_metadata(storage):
    """Test storing SSP metadata."""
    sample_metadata = {
        "title": "Test SSP",
        "version": "1.0",
        "last-modified": "2023-01-01T00:00:00Z",
        "system-name": "Test System"
    }
    
    scan_id = storage.store_ssp_metadata("/path/to/ssp.json", sample_metadata)
    assert scan_id > 0
    
    # Verify the data was stored
    stored_data = storage.get_scan(scan_id)
    assert stored_data is not None
    assert stored_data["ssp_path"] == "/path/to/ssp.json"
    assert stored_data["filename"] == "ssp.json"
    assert "scan_date" in stored_data
    assert stored_data["metadata"] == sample_metadata


def test_store_controls(storage):
    """Test storing control data."""
    # First, store an SSP to get a scan ID
    scan_id = storage.store_ssp_metadata("/path/to/ssp.json", {"title": "Test SSP"})
    
    # Sample controls
    sample_controls = [
        {
            "control-id": "AC-1",
            "statements": [{"statement-id": "AC-1.1", "description": "Test statement"}]
        },
        {
            "control-id": "AU-2",
            "statements": [{"statement-id": "AU-2.1", "description": "Test statement"}]
        }
    ]
    
    control_ids = storage.store_controls(scan_id, sample_controls)
    assert len(control_ids) == 2
    
    # Verify the controls were stored with the scan ID
    stored_controls = storage.get_controls_for_scan(scan_id)
    assert len(stored_controls) == 2
    assert stored_controls[0]["scan_id"] == scan_id
    assert stored_controls[1]["scan_id"] == scan_id
    
    # Verify control IDs
    control_ids = [c["control-id"] for c in stored_controls]
    assert "AC-1" in control_ids
    assert "AU-2" in control_ids


def test_store_gaps(storage):
    """Test storing gap data."""
    # First, store an SSP to get a scan ID
    scan_id = storage.store_ssp_metadata("/path/to/ssp.json", {"title": "Test SSP"})
    
    # Sample gaps
    sample_gaps = [
        {
            "control-id": "CM-6",
            "title": "Configuration Settings",
            "impact": "Medium",
            "effort": "L",
            "guidance": "Test guidance"
        },
        {
            "control-id": "IA-2",
            "title": "Identification and Authentication",
            "impact": "High",
            "effort": "M",
            "guidance": "Test guidance"
        }
    ]
    
    gap_ids = storage.store_gaps(scan_id, sample_gaps)
    assert len(gap_ids) == 2
    
    # Verify the gaps were stored with the scan ID
    stored_gaps = storage.get_gaps_for_scan(scan_id)
    assert len(stored_gaps) == 2
    assert stored_gaps[0]["scan_id"] == scan_id
    assert stored_gaps[1]["scan_id"] == scan_id
    
    # Verify gap control IDs
    gap_control_ids = [g["control-id"] for g in stored_gaps]
    assert "CM-6" in gap_control_ids
    assert "IA-2" in gap_control_ids


def test_export_scan_results(storage, temp_dir):
    """Test exporting scan results to JSON."""
    # Create a complete scan with controls and gaps
    scan_id = storage.store_ssp_metadata("/path/to/ssp.json", {"title": "Test SSP"})
    
    sample_controls = [
        {"control-id": "AC-1", "statements": [{"statement-id": "AC-1.1", "description": "Test"}]}
    ]
    storage.store_controls(scan_id, sample_controls)
    
    sample_gaps = [
        {"control-id": "CM-6", "title": "Configuration Settings"}
    ]
    storage.store_gaps(scan_id, sample_gaps)
    
    # Export the results
    output_path = os.path.join(temp_dir, "export.json")
    export_path = storage.export_scan_results(scan_id, output_path)
    
    # Verify the export file exists
    assert os.path.exists(export_path)
    
    # Verify the export content
    with open(export_path, 'r') as f:
        exported_data = json.load(f)
    
    assert "scan" in exported_data
    assert "controls" in exported_data
    assert "gaps" in exported_data
    assert exported_data["scan"]["metadata"]["title"] == "Test SSP"
    assert len(exported_data["controls"]) == 1
    assert len(exported_data["gaps"]) == 1
    assert exported_data["controls"][0]["control-id"] == "AC-1"
    assert exported_data["gaps"][0]["control-id"] == "CM-6"