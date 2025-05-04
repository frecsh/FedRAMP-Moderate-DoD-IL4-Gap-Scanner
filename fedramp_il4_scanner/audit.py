"""Audit logging module for FedRAMP IL4 Scanner.

This module provides comprehensive audit logging capabilities to track
all scanner operations and maintain a clear audit trail.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

class AuditLogger:
    """Audit logger for tracking scanner operations."""
    
    def __init__(self, log_path: Optional[str] = None):
        """Initialize the audit logger.
        
        Args:
            log_path: Optional custom path for the audit log file
        """
        if log_path is None:
            # Create logs directory if it doesn't exist
            log_dir = Path.home() / ".fedramp_il4_scanner" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = str(log_dir / f"audit_{timestamp}.log")
        
        # Configure loguru logger
        logger.remove()  # Remove default handler
        
        # Add file handler for audit logs
        logger.add(
            log_path,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            rotation="10 MB",
            retention="1 month",
            level="DEBUG"
        )
        
        # Add console handler for user feedback
        logger.add(
            lambda msg: print(msg, end=""),
            format="<level>{level}</level>: {message}",
            level="INFO"
        )
        
        self.log_path = log_path
        logger.info(f"Audit logging initialized at {log_path}")
    
    def log_scan_start(self, ssp_path: str, mapping_path: str) -> None:
        """Log the start of a scan operation.
        
        Args:
            ssp_path: Path to the SSP file
            mapping_path: Path to the mapping file
        """
        logger.info(f"Starting scan of {ssp_path} with mapping {mapping_path}")
        logger.debug(f"Scan parameters: ssp={ssp_path}, mapping={mapping_path}")
    
    def log_scan_complete(self, ssp_path: str, controls_count: int, gaps_count: int) -> None:
        """Log the completion of a scan operation.
        
        Args:
            ssp_path: Path to the scanned SSP file
            controls_count: Number of controls analyzed
            gaps_count: Number of gaps identified
        """
        logger.info(f"Scan complete for {ssp_path}")
        logger.info(f"Analyzed {controls_count} controls, identified {gaps_count} gaps")
    
    def log_validation_result(self, file_path: str, success: bool, details: Dict[str, Any]) -> None:
        """Log OSCAL validation results.
        
        Args:
            file_path: Path to the validated file
            success: Whether validation succeeded
            details: Details about the validation result
        """
        if success:
            logger.info(f"OSCAL validation successful for {os.path.basename(file_path)}")
            logger.debug(f"Validation details: {json.dumps(details)}")
        else:
            logger.error(f"OSCAL validation failed for {os.path.basename(file_path)}")
            logger.error(f"Validation error: {details.get('error', 'Unknown error')}")
    
    def log_control_extraction(self, file_path: str, controls_count: int) -> None:
        """Log control extraction results.
        
        Args:
            file_path: Path to the SSP file
            controls_count: Number of controls extracted
        """
        logger.info(f"Extracted {controls_count} controls from {os.path.basename(file_path)}")
    
    def log_gap_analysis(self, gaps_count: int, missing_controls: list) -> None:
        """Log gap analysis results.
        
        Args:
            gaps_count: Number of gaps identified
            missing_controls: List of missing control IDs
        """
        logger.info(f"Gap analysis complete: {gaps_count} gaps identified")
        if gaps_count > 0:
            logger.debug(f"Missing controls: {', '.join(missing_controls)}")
    
    def log_report_generation(self, output_path: str) -> None:
        """Log report generation.
        
        Args:
            output_path: Path to the generated report
        """
        logger.info(f"Report generated at {output_path}")
    
    def log_error(self, operation: str, error: Exception) -> None:
        """Log an error during operation.
        
        Args:
            operation: The operation during which the error occurred
            error: The error that occurred
        """
        logger.error(f"Error during {operation}: {str(error)}")
        logger.exception(error)
    
    def get_log_path(self) -> str:
        """Get the path to the current audit log file.
        
        Returns:
            str: Path to the audit log file
        """
        return self.log_path