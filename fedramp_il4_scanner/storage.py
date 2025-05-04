"""Storage module for FedRAMP IL4 Scanner.

This module provides a TinyDB-based storage solution for SSP data and scan results.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

class ScanStorage:
    """Storage class for scan data using TinyDB."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage with optional custom database path.
        
        Args:
            db_path: Optional path to the database file. If not provided,
                     a default path will be used.
        """
        if db_path is None:
            # Create data directory if it doesn't exist
            data_dir = Path.home() / ".fedramp_il4_scanner"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "scan_data.json")
        
        logger.debug(f"Initializing TinyDB storage at {db_path}")
        self.db = TinyDB(db_path, storage=CachingMiddleware(JSONStorage))
        self.scans = self.db.table("scans")
        self.controls = self.db.table("controls")
        self.gaps = self.db.table("gaps")
    
    def store_ssp_metadata(self, ssp_path: str, metadata: Dict[str, Any]) -> int:
        """Store SSP metadata.
        
        Args:
            ssp_path: Path to the SSP file
            metadata: Metadata extracted from the SSP
        
        Returns:
            int: The inserted document ID
        """
        scan_data = {
            "ssp_path": ssp_path,
            "filename": os.path.basename(ssp_path),
            "scan_date": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        return self.scans.insert(scan_data)
    
    def store_controls(self, scan_id: int, controls: List[Dict[str, Any]]) -> List[int]:
        """Store control data for a specific scan.
        
        Args:
            scan_id: The ID of the parent scan
            controls: List of control data dictionaries
        
        Returns:
            List[int]: The list of inserted document IDs
        """
        for control in controls:
            control["scan_id"] = scan_id
        
        return self.controls.insert_multiple(controls)
    
    def store_gaps(self, scan_id: int, gaps: List[Dict[str, Any]]) -> List[int]:
        """Store gap data for a specific scan.
        
        Args:
            scan_id: The ID of the parent scan
            gaps: List of gap data dictionaries
        
        Returns:
            List[int]: The list of inserted document IDs
        """
        for gap in gaps:
            gap["scan_id"] = scan_id
        
        return self.gaps.insert_multiple(gaps)
    
    def get_scan(self, scan_id: int) -> Dict[str, Any]:
        """Retrieve a specific scan by ID.
        
        Args:
            scan_id: The ID of the scan to retrieve
        
        Returns:
            Dict[str, Any]: The scan data
        """
        return self.scans.get(doc_id=scan_id)
    
    def get_controls_for_scan(self, scan_id: int) -> List[Dict[str, Any]]:
        """Retrieve all controls for a specific scan.
        
        Args:
            scan_id: The ID of the scan
        
        Returns:
            List[Dict[str, Any]]: The list of controls
        """
        Control = Query()
        return self.controls.search(Control.scan_id == scan_id)
    
    def get_gaps_for_scan(self, scan_id: int) -> List[Dict[str, Any]]:
        """Retrieve all gaps for a specific scan.
        
        Args:
            scan_id: The ID of the scan
        
        Returns:
            List[Dict[str, Any]]: The list of gaps
        """
        Gap = Query()
        return self.gaps.search(Gap.scan_id == scan_id)
    
    def export_scan_results(self, scan_id: int, output_path: str) -> str:
        """Export complete scan results to a JSON file.
        
        Args:
            scan_id: The ID of the scan to export
            output_path: Path where the file should be saved
        
        Returns:
            str: Path to the exported file
        """
        scan = self.get_scan(scan_id)
        controls = self.get_controls_for_scan(scan_id)
        gaps = self.get_gaps_for_scan(scan_id)
        
        results = {
            "scan": scan,
            "controls": controls,
            "gaps": gaps
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return output_path