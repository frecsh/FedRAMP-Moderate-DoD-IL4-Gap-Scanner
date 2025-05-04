"""Main scanner module for FedRAMP IL4 Scanner.

This module orchestrates the scanning process, combining validation, 
control extraction, gap analysis, and reporting.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from fedramp_il4_scanner.analyzer import GapAnalyzer
from fedramp_il4_scanner.audit import AuditLogger
from fedramp_il4_scanner.storage import ScanStorage
from fedramp_il4_scanner.validation import OscalValidator


class IL4Scanner:
    """Main scanner class for FedRAMP to IL4 gap analysis."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize the scanner.
        
        Args:
            audit_logger: Optional audit logger to use
        """
        self.audit_logger = audit_logger or AuditLogger()
        self.validator = OscalValidator()
        self.storage = ScanStorage()
        logger.debug("IL4Scanner initialized")
    
    def scan(self, ssp_path: str, mapping_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run the full scan process.
        
        Args:
            ssp_path: Path to the SSP file
            mapping_path: Path to the mapping file
            output_dir: Optional output directory for reports
            
        Returns:
            Dict[str, Any]: Scan results summary
        """
        start_time = time.time()
        
        # Log scan start
        self.audit_logger.log_scan_start(ssp_path, mapping_path)
        
        try:
            # Validate SSP
            valid, details = self.validator.validate_file(ssp_path)
            self.audit_logger.log_validation_result(ssp_path, valid, details)
            
            if not valid:
                raise ValueError(f"Invalid OSCAL SSP: {details.get('error', 'Unknown validation error')}")
            
            try:
                # Extract SSP metadata
                metadata = self.validator.get_ssp_metadata(ssp_path)
                if not metadata:
                    raise ValueError("Failed to extract metadata from SSP")
            except Exception as e:
                self.audit_logger.log_error("get_ssp_metadata", e)
                raise ValueError(f"Metadata error: {str(e)}")
            
            # Store SSP metadata
            scan_id = self.storage.store_ssp_metadata(ssp_path, metadata)
            
            try:
                # Extract controls
                controls = self.validator.extract_controls(ssp_path)
                if controls is None:
                    controls = []
                self.audit_logger.log_control_extraction(ssp_path, len(controls))
            except Exception as e:
                self.audit_logger.log_error("extract_controls", e)
                raise ValueError(f"Control error: {str(e)}")
            
            # Store controls
            self.storage.store_controls(scan_id, controls)
            
            try:
                # Create gap analyzer
                analyzer = GapAnalyzer(mapping_path)
                
                # Ensure mapping file integrity
                mapping_valid = analyzer.verify_mapping_integrity()
                if not mapping_valid:
                    raise ValueError("Mapping file integrity check failed")
            except ValueError as e:
                # Pass through ValueError directly
                raise
            except Exception as e:
                self.audit_logger.log_error("verify_mapping_integrity", e)
                raise ValueError(f"Mapping error: {str(e)}")
            
            try:
                # Analyze gaps
                gaps = analyzer.analyze_gaps(controls)
                
                # Get control metrics
                metrics = analyzer.get_control_metrics(controls)
            except Exception as e:
                self.audit_logger.log_error("analyze_gaps", e)
                raise ValueError(f"Analysis error: {str(e)}")
            
            # Store gaps
            self.storage.store_gaps(scan_id, gaps)
            
            # Generate output directory if not provided
            if output_dir is None:
                output_dir = Path.cwd() / "reports" / f"scan_{scan_id}"
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Export raw gap report
            gap_json_path = str(output_dir / "gap_raw.json")
            self._export_gap_json(gaps, metrics, gap_json_path)
            
            # Log completion
            missing_controls = [gap["control-id"] for gap in gaps]
            self.audit_logger.log_gap_analysis(len(gaps), missing_controls)
            
            # Prepare result summary
            elapsed_time = time.time() - start_time
            result = {
                "scan_id": scan_id,
                "status": "success",
                "ssp_file": ssp_path,
                "mapping_file": mapping_path,
                "controls_analyzed": len(controls),
                "gaps_identified": len(gaps),
                "compliance_percentage": metrics["compliance_percentage"],
                "elapsed_time": round(elapsed_time, 2),
                "report_path": str(output_dir)
            }
            
            self.audit_logger.log_scan_complete(ssp_path, len(controls), len(gaps))
            
            return result
            
        except Exception as e:
            self.audit_logger.log_error("scan", e)
            raise
    
    def _export_gap_json(self, gaps: List[Dict[str, Any]], metrics: Dict[str, Any], 
                         output_path: str) -> str:
        """Export gap analysis to JSON.
        
        Args:
            gaps: List of identified gaps
            metrics: Control metrics
            output_path: Path where the JSON file should be saved
            
        Returns:
            str: Path to the exported file
        """
        data = {
            "gaps": gaps,
            "metrics": metrics,
            "generated_at": time.time(),
            "version": "0.1.0"
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path