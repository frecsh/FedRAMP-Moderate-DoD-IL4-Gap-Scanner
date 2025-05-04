"""Tests for the CLI module."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from fedramp_il4_scanner.cli import app
from fedramp_il4_scanner.scanner import IL4Scanner


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@patch('fedramp_il4_scanner.scanner.IL4Scanner.scan')
def test_scan_command_success(mock_scan, cli_runner, sample_ssp_path, sample_mapping_path, temp_dir):
    """Test the scan command with successful execution."""
    # Configure mock to return a success result
    mock_scan.return_value = {
        "scan_id": 1,
        "status": "success",
        "ssp_file": sample_ssp_path,
        "mapping_file": sample_mapping_path,
        "controls_analyzed": 10,
        "gaps_identified": 3,
        "compliance_percentage": 70.0,
        "elapsed_time": 1.5,
        "report_path": temp_dir
    }
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["scan", sample_ssp_path, "--mapping", sample_mapping_path, "--output", temp_dir])
    
    # Check the result
    assert result.exit_code == 0
    assert "Scan Complete" in result.stdout
    assert "Controls Analyzed: 10" in result.stdout
    assert "Gaps Identified: 3" in result.stdout
    assert "70.0%" in result.stdout
    
    # Verify mock was called with correct arguments
    mock_scan.assert_called_once_with(sample_ssp_path, sample_mapping_path, temp_dir)


@patch('os.path.exists')
def test_scan_command_file_not_found(mock_exists, cli_runner, temp_dir):
    """Test the scan command with a non-existent SSP file."""
    nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
    
    # Mock os.path.exists to return False for the SSP file
    mock_exists.return_value = False
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["scan", nonexistent_file])
    
    # Check the result
    assert result.exit_code == 1
    assert "ERROR" in result.stdout
    assert "SSP file not found" in result.stdout


@patch('os.path.exists')
@patch('fedramp_il4_scanner.scanner.IL4Scanner.scan')
def test_scan_command_with_error(mock_scan, mock_exists, cli_runner, sample_ssp_path, sample_mapping_path):
    """Test the scan command when an error occurs during scanning."""
    # Configure mocks
    mock_exists.return_value = True
    mock_scan.side_effect = ValueError("Invalid SSP format")
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["scan", sample_ssp_path, "--mapping", sample_mapping_path])
    
    # Check the result
    assert result.exit_code == 1
    assert "ERROR" in result.stdout
    assert "Invalid SSP format" in result.stdout


@patch('os.path.exists')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.verify_mapping_integrity')
def test_verify_mapping_command_success(mock_verify, mock_exists, cli_runner, sample_mapping_path):
    """Test the verify-mapping command with a valid mapping file."""
    # Configure mocks
    mock_exists.return_value = True
    mock_verify.return_value = True
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["verify-mapping", sample_mapping_path])
    
    # Check the result
    assert result.exit_code == 0
    assert "VALID" in result.stdout
    assert "passed integrity checks" in result.stdout


@patch('os.path.exists')
@patch('fedramp_il4_scanner.analyzer.GapAnalyzer.verify_mapping_integrity')
def test_verify_mapping_command_failure(mock_verify, mock_exists, cli_runner, sample_mapping_path):
    """Test the verify-mapping command with an invalid mapping file."""
    # Configure mocks
    mock_exists.return_value = True
    mock_verify.return_value = False
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["verify-mapping", sample_mapping_path])
    
    # Check the result
    assert result.exit_code == 1
    assert "INVALID" in result.stdout
    assert "failed integrity checks" in result.stdout


@patch('os.path.exists')
def test_verify_mapping_command_file_not_found(mock_exists, cli_runner, temp_dir):
    """Test the verify-mapping command with a non-existent mapping file."""
    nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
    
    # Mock os.path.exists to return False
    mock_exists.return_value = False
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["verify-mapping", nonexistent_file])
    
    # Check the result
    assert result.exit_code == 1
    assert "ERROR" in result.stdout
    assert "not found" in result.stdout


@patch('os.path.exists')
@patch('typer.prompt')
@patch('fedramp_il4_scanner.scanner.IL4Scanner.scan')
def test_wizard_command(mock_scan, mock_prompt, mock_exists, cli_runner, 
                       sample_ssp_path, sample_mapping_path, temp_dir):
    """Test the wizard command with user input."""
    # Configure mocks
    mock_exists.return_value = True
    mock_prompt.side_effect = [sample_ssp_path, sample_mapping_path, temp_dir]
    mock_scan.return_value = {
        "scan_id": 1,
        "status": "success",
        "controls_analyzed": 5,
        "gaps_identified": 2,
        "compliance_percentage": 60.0,
        "report_path": temp_dir
    }
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["wizard"])
    
    # Check the result
    assert result.exit_code == 0
    assert "FedRAMP Moderate → DoD IL4 Gap Scanner Wizard" in result.stdout
    assert "Controls Analyzed: 5" in result.stdout
    
    # Verify scan was called with correct arguments
    mock_scan.assert_called_once_with(sample_ssp_path, sample_mapping_path, temp_dir)


@patch('os.path.exists')
@patch('typer.prompt')
def test_wizard_command_with_nonexistent_file(mock_prompt, mock_exists, cli_runner, temp_dir):
    """Test the wizard command when user provides non-existent file."""
    nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
    
    # Configure mocks - first file exists check fails, other file would exist
    mock_exists.side_effect = lambda path: path != nonexistent_file
    mock_prompt.return_value = nonexistent_file
    
    # Run the CLI command
    result = cli_runner.invoke(app, ["wizard"])
    
    # Check the result
    assert result.exit_code == 1
    assert "ERROR" in result.stdout
    assert "File not found" in result.stdout