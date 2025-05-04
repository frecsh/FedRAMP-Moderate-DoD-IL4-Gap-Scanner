"""Gap analysis module for FedRAMP IL4 Scanner.

This module compares FedRAMP Moderate controls with DoD IL4 requirements
to identify compliance gaps.
"""

import json
import os
from typing import Any, Dict, List, Set, Tuple

from loguru import logger

class GapAnalyzer:
    """Analyzer for identifying FedRAMP to DoD IL4 gaps."""
    
    def __init__(self, mapping_path: str):
        """Initialize the gap analyzer.
        
        Args:
            mapping_path: Path to the control mapping file
        """
        self.mapping_path = mapping_path
        self.mapping_data = self._load_mapping(mapping_path)
        logger.debug(f"Gap analyzer initialized with mapping file: {mapping_path}")
    
    def _load_mapping(self, mapping_path: str) -> Dict[str, Any]:
        """Load control mapping from file.
        
        Args:
            mapping_path: Path to the mapping file
        
        Returns:
            Dict[str, Any]: The loaded mapping data
        """
        if not os.path.exists(mapping_path):
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        
        try:
            with open(mapping_path, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid mapping file format: {str(e)}")
    
    def analyze_gaps(self, implemented_controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze gaps between implemented controls and IL4 requirements.
        
        Args:
            implemented_controls: List of controls implemented in the SSP
            
        Returns:
            List[Dict[str, Any]]: List of identified gaps
        """
        # Extract just the control IDs from implemented controls
        implemented_ids = {control.get("control-id") for control in implemented_controls}
        
        # Get required IL4 controls from mapping
        required_controls = self._get_required_il4_controls()
        
        # Find missing controls
        gaps = []
        for control_id, details in required_controls.items():
            if control_id not in implemented_ids:
                gaps.append({
                    "control-id": control_id,
                    "title": details.get("title", ""),
                    "description": details.get("description", ""),
                    "impact": details.get("impact", "Medium"),
                    "effort": details.get("effort", "M"),
                    "guidance": details.get("guidance", "")
                })
        
        return gaps
    
    def _get_required_il4_controls(self) -> Dict[str, Dict[str, Any]]:
        """Extract required IL4 controls from the mapping.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of required IL4 controls
        """
        required_controls = {}
        
        # Extract controls requiring different implementation for IL4
        for control_id, mapping in self.mapping_data.get("mappings", {}).items():
            # Include if control is marked as IL4-specific or has delta
            if mapping.get("required_for_il4", False) or mapping.get("has_il4_delta", False):
                required_controls[control_id] = {
                    "title": mapping.get("title", ""),
                    "description": mapping.get("description", ""),
                    "impact": mapping.get("security_impact", "Medium"),
                    "effort": mapping.get("implementation_effort", "M"),
                    "guidance": mapping.get("remediation_guidance", "")
                }
        
        return required_controls
    
    def get_control_metrics(self, implemented_controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics about control implementation status.
        
        Args:
            implemented_controls: List of controls implemented in the SSP
            
        Returns:
            Dict[str, Any]: Metrics about control implementation
        """
        implemented_ids = {control.get("control-id") for control in implemented_controls}
        required_controls = self._get_required_il4_controls()
        
        total_required = len(required_controls)
        total_implemented = sum(1 for ctrl_id in required_controls if ctrl_id in implemented_ids)
        total_missing = total_required - total_implemented
        
        # Categorize by impact
        impact_counts = {"High": 0, "Medium": 0, "Low": 0}
        for ctrl_id, details in required_controls.items():
            if ctrl_id not in implemented_ids:
                impact = details.get("impact", "Medium")
                impact_counts[impact] = impact_counts.get(impact, 0) + 1
        
        # Calculate compliance percentage
        compliance_pct = (total_implemented / total_required * 100) if total_required > 0 else 0
        
        return {
            "total_required": total_required,
            "total_implemented": total_implemented,
            "total_missing": total_missing,
            "compliance_percentage": round(compliance_pct, 1),
            "missing_by_impact": impact_counts
        }
    
    def verify_mapping_integrity(self) -> bool:
        """Verify the integrity of the mapping file.
        
        Returns:
            bool: Whether the mapping file integrity check passed
        """
        # For now, just check that the file exists and has expected structure
        # In a real implementation, this would verify checksums, digital signatures, etc.
        
        if not os.path.exists(self.mapping_path):
            logger.error(f"Mapping file not found: {self.mapping_path}")
            return False
        
        required_keys = ["mappings", "metadata"]
        try:
            with open(self.mapping_path, 'r') as f:
                data = json.load(f)
                
            for key in required_keys:
                if key not in data:
                    logger.error(f"Missing required key in mapping file: {key}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Error verifying mapping file: {str(e)}")
            return False