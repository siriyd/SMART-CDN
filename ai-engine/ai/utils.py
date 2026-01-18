"""
AI Engine Utilities
Helper functions for data processing and validation
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def validate_request_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean request logs.
    
    Args:
        logs: Raw request logs
    
    Returns:
        Validated and cleaned logs
    """
    validated = []
    required_fields = ["content_id", "request_timestamp"]
    
    for log in logs:
        if not isinstance(log, dict):
            continue
        
        # Check required fields
        if all(field in log for field in required_fields):
            validated.append(log)
        else:
            logger.warning(f"Skipping invalid log entry: missing required fields")
    
    return validated


def validate_content_metadata(metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean content metadata.
    
    Args:
        metadata: Raw content metadata
    
    Returns:
        Validated metadata
    """
    validated = []
    required_fields = ["content_id"]
    
    for item in metadata:
        if not isinstance(item, dict):
            continue
        
        if all(field in item for field in required_fields):
            validated.append(item)
        else:
            logger.warning(f"Skipping invalid metadata entry: missing required fields")
    
    return validated


def validate_edge_constraints(constraints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean edge constraints.
    
    Args:
        constraints: Raw edge constraints
    
    Returns:
        Validated constraints
    """
    validated = []
    required_fields = ["edge_id"]
    
    for constraint in constraints:
        if not isinstance(constraint, dict):
            continue
        
        if all(field in constraint for field in required_fields):
            # Ensure numeric fields are valid
            if "cache_capacity_mb" in constraint:
                try:
                    constraint["cache_capacity_mb"] = int(constraint["cache_capacity_mb"])
                except:
                    constraint["cache_capacity_mb"] = 100
            
            if "current_usage_mb" in constraint:
                try:
                    constraint["current_usage_mb"] = int(constraint["current_usage_mb"])
                except:
                    constraint["current_usage_mb"] = 0
            
            validated.append(constraint)
        else:
            logger.warning(f"Skipping invalid edge constraint: missing required fields")
    
    return validated
