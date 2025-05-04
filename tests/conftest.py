"""Test configuration for pytest.

This file contains pytest fixtures, configuration, and hooks that are
shared across all test files.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest


# Register custom markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "integration: mark a test as an integration test that tests multiple components together"
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def audit_logger():
    """Create a mock audit logger for testing."""
    from fedramp_il4_scanner.audit import AuditLogger
    
    # Create a temporary directory for the log
    with tempfile.TemporaryDirectory() as tmpdirname:
        log_path = os.path.join(tmpdirname, "audit.log")
        logger = AuditLogger(log_path=log_path)
        yield logger


@pytest.fixture
def sample_ssp_path():
    """Get the path to a sample SSP file."""
    # Use a sample SSP file in the sample_ssp directory
    sample_path = Path(__file__).parent.parent / "sample_ssp" / "sample_fedramp_ssp.json"
    
    # If the file doesn't exist, create a minimal one for testing
    if not sample_path.exists():
        sample_path.parent.mkdir(exist_ok=True)
        
        # Create a minimal SSP
        minimal_ssp = {
            "oscal-version": "1.0.0",
            "system-security-plan": {
                "metadata": {
                    "title": "Test SSP",
                    "version": "1.0"
                },
                "system-characteristics": {
                    "system-name": "Test System",
                    "system-id": "TEST-01"
                },
                "control-implementation": {
                    "implemented-requirements": [
                        {
                            "control-id": "AC-1",
                            "statements": [
                                {
                                    "statement-id": "AC-1.1",
                                    "description": "Test implementation"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        with open(sample_path, 'w') as f:
            json.dump(minimal_ssp, f, indent=2)
    
    return str(sample_path)


@pytest.fixture
def sample_mapping_path():
    """Get the path to a sample mapping file."""
    # Use a sample mapping file in the mappings directory
    sample_path = Path(__file__).parent.parent / "mappings" / "fedramp_il4.json"
    
    # If the file doesn't exist, create a minimal one for testing
    if not sample_path.exists():
        sample_path.parent.mkdir(exist_ok=True)
        
        # Create a minimal mapping
        minimal_mapping = {
            "metadata": {
                "title": "FedRAMP Moderate to IL4 Mapping",
                "version": "1.0",
                "description": "Test mapping file"
            },
            "mappings": {
                "AC-1": {
                    "title": "Access Control Policy and Procedures",
                    "required_for_il4": True,
                    "gap_details": "IL4 requires additional documentation"
                },
                "AC-2": {
                    "title": "Account Management",
                    "required_for_il4": True,
                    "gap_details": "IL4 requires additional controls"
                },
                "AU-2": {
                    "title": "Audit Events",
                    "required_for_il4": True,
                    "gap_details": "No significant changes"
                }
            }
        }
        
        with open(sample_path, 'w') as f:
            json.dump(minimal_mapping, f, indent=2)
    
    return str(sample_path)