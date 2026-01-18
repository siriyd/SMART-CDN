"""
Popularity Predictor
Local time-series forecasting for content popularity
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import statistics

logger = logging.getLogger(__name__)


class PopularityPredictor:
    """Simple popularity predictor using exponential smoothing and trend detection"""
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.2):
        """
        Initialize predictor with smoothing parameters.
        
        Args:
            alpha: Exponential smoothing factor for level (0-1)
            beta: Trend smoothing factor (0-1)
        """
        self.alpha = alpha
        self.beta = beta
    
    def predict(
        self,
        request_logs: List[Dict[str, Any]],
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Predict popularity for content based on request logs.
        
        Args:
            request_logs: List of request log dictionaries with:
                - content_id: str
                - request_timestamp: datetime or ISO string
                - is_cache_hit: bool
            time_window_minutes: Prediction window in minutes
        
        Returns:
            List of popularity forecasts with:
                - content_id: str
                - predicted_requests_next_window: int
                - confidence: float (0-1)
        """
        if not request_logs:
            logger.warning("No request logs provided for prediction")
            return []
        
        # Group requests by content_id and time window
        content_requests = defaultdict(list)
        
        for log in request_logs:
            content_id = str(log.get("content_id", ""))
            if not content_id:
                continue
            
            # Parse timestamp and ensure it's timezone-aware (UTC)
            timestamp = log.get("request_timestamp")
            if isinstance(timestamp, str):
                try:
                    # Parse ISO format string
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    # Explicitly ensure UTC timezone
                    if timestamp.tzinfo is None:
                        # Naive datetime - assume UTC
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    else:
                        # Convert to UTC if not already (handles any timezone)
                        timestamp = timestamp.astimezone(timezone.utc)
                except Exception as e:
                    logger.debug(f"Failed to parse timestamp string '{timestamp}': {e}")
                    continue
            elif isinstance(timestamp, datetime):
                # Normalize datetime object to UTC
                if timestamp.tzinfo is None:
                    # Naive datetime - assume UTC
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                else:
                    # Convert to UTC if not already
                    timestamp = timestamp.astimezone(timezone.utc)
            else:
                logger.debug(f"Invalid timestamp type: {type(timestamp)}")
                continue
            
            content_requests[content_id].append(timestamp)
        
        # Calculate predictions for each content
        forecasts = []
        # Use timezone-aware UTC datetime
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=time_window_minutes)
        
        for content_id, timestamps in content_requests.items():
            # Filter to recent window
            # Ensure all timestamps are timezone-aware before comparison
            try:
                recent_timestamps = [
                    ts for ts in timestamps 
                    if ts.tzinfo is not None and ts >= window_start
                ]
            except TypeError as e:
                logger.error(
                    f"Datetime comparison error for content {content_id}: {e}. "
                    f"Timestamp types: {[type(ts).__name__ for ts in timestamps[:3]]}"
                )
                # Fallback: skip this content
                continue
            
            if not recent_timestamps:
                # No recent requests, predict low
                forecasts.append({
                    "content_id": content_id,
                    "predicted_requests_next_window": 0,
                    "confidence": 0.1
                })
                continue
            
            # Sort timestamps
            recent_timestamps.sort()
            
            # Calculate request rate (requests per minute)
            # All timestamps should be timezone-aware at this point
            try:
                if len(recent_timestamps) > 1:
                    # Ensure both timestamps are timezone-aware
                    ts_start = recent_timestamps[0]
                    ts_end = recent_timestamps[-1]
                    if ts_start.tzinfo is None or ts_end.tzinfo is None:
                        logger.warning(
                            f"Naive datetime found in calculations for {content_id}, "
                            f"normalizing to UTC"
                        )
                        if ts_start.tzinfo is None:
                            ts_start = ts_start.replace(tzinfo=timezone.utc)
                        if ts_end.tzinfo is None:
                            ts_end = ts_end.replace(tzinfo=timezone.utc)
                    
                    time_span = (ts_end - ts_start).total_seconds() / 60
                    if time_span > 0:
                        rate = len(recent_timestamps) / time_span
                    else:
                        rate = len(recent_timestamps)
                else:
                    rate = 1.0
            except TypeError as e:
                logger.error(
                    f"Time calculation error for content {content_id}: {e}. "
                    f"Using default rate."
                )
                rate = 1.0
            
            # Simple exponential smoothing for trend
            # Use last N requests to detect trend
            try:
                if len(recent_timestamps) >= 3:
                    # Split into two halves
                    mid = len(recent_timestamps) // 2
                    ts_0 = recent_timestamps[0]
                    ts_mid = recent_timestamps[mid]
                    ts_end = recent_timestamps[-1]
                    
                    # Ensure all timestamps are timezone-aware
                    if ts_0.tzinfo is None:
                        ts_0 = ts_0.replace(tzinfo=timezone.utc)
                    if ts_mid.tzinfo is None:
                        ts_mid = ts_mid.replace(tzinfo=timezone.utc)
                    if ts_end.tzinfo is None:
                        ts_end = ts_end.replace(tzinfo=timezone.utc)
                    
                    first_half_rate = mid / max(
                        (ts_mid - ts_0).total_seconds() / 60,
                        1
                    )
                    second_half_rate = (len(recent_timestamps) - mid) / max(
                        (ts_end - ts_mid).total_seconds() / 60,
                        1
                    )
                    
                    # Trend detection
                    trend = second_half_rate - first_half_rate
                    predicted_rate = rate + (trend * self.beta)
                else:
                    predicted_rate = rate
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"Trend calculation error for content {content_id}: {e}. "
                    f"Using base rate."
                )
                predicted_rate = rate
            
            # Predict requests for next window
            predicted_requests = max(0, int(predicted_rate * time_window_minutes))
            
            # Calculate confidence based on data quality
            # Lowered thresholds to ensure forecasts are generated with minimal data
            if len(recent_timestamps) >= 10:
                confidence = 0.9
            elif len(recent_timestamps) >= 5:
                confidence = 0.7
            elif len(recent_timestamps) >= 2:
                confidence = 0.5
            elif len(recent_timestamps) >= 1:
                confidence = 0.3  # Lowered from requiring 2+ to allow single request
            else:
                confidence = 0.2  # Even with minimal data, provide a forecast
            
            forecasts.append({
                "content_id": content_id,
                "predicted_requests_next_window": int(predicted_requests),
                "confidence": round(confidence, 2)
            })
        
        logger.info(f"Generated {len(forecasts)} popularity forecasts")
        return forecasts
    
    def predict_with_metadata(
        self,
        request_logs: List[Dict[str, Any]],
        content_metadata: List[Dict[str, Any]],
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Predict popularity with content metadata consideration.
        
        Args:
            request_logs: Request logs
            content_metadata: Content metadata with size_kb, category, etc.
            time_window_minutes: Prediction window
        
        Returns:
            Enhanced forecasts with metadata adjustments
        """
        # Get base predictions
        forecasts = self.predict(request_logs, time_window_minutes)
        
        # Create metadata lookup
        metadata_lookup = {
            str(item.get("content_id", "")): item
            for item in content_metadata
        }
        
        # Adjust predictions based on metadata
        for forecast in forecasts:
            content_id = forecast["content_id"]
            metadata = metadata_lookup.get(content_id, {})
            
            # Adjust based on content type (videos tend to be more popular)
            content_type = metadata.get("content_type", "")
            if content_type == "video":
                forecast["predicted_requests_next_window"] = int(
                    forecast["predicted_requests_next_window"] * 1.2
                )
            elif content_type == "image":
                forecast["predicted_requests_next_window"] = int(
                    forecast["predicted_requests_next_window"] * 0.8
                )
            
            # Adjust confidence based on content size (larger content = less likely to be cached)
            size_kb = metadata.get("size_kb", 0)
            if size_kb > 5000:  # Large content
                forecast["confidence"] = max(0.1, forecast["confidence"] - 0.1)
        
        return forecasts
