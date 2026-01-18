# Datetime Timezone Fixes - AI Engine

## Issues Fixed

### 1. Naive vs Aware Datetime Comparisons
**Problem**: `datetime.utcnow()` returns naive datetimes, causing comparison errors with timezone-aware datetimes.

**Fixes Applied**:
- `predictor.py` line 93: Changed `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `schemas.py` line 46: Changed `datetime.utcnow` → `lambda: datetime.now(timezone.utc)`
- Added timezone normalization for all incoming timestamps

### 2. Timestamp Normalization
**Problem**: Incoming timestamps may be naive or aware, causing comparison failures.

**Fixes Applied**:
- All string timestamps are parsed and normalized to UTC
- All datetime objects are checked and normalized to UTC if needed
- Added explicit timezone checks before comparisons

### 3. Exception Logging
**Problem**: Errors were not logged with sufficient detail for debugging.

**Fixes Applied**:
- Added `exc_info=True` to all error logs
- Added file name and line number logging
- Added payload size logging (not raw data)
- Added full traceback logging
- Added exception type logging

### 4. Error Handling
**Problem**: `/decide` endpoint could crash silently or return generic errors.

**Fixes Applied**:
- Wrapped each major operation in try/except
- Return structured error responses
- Continue processing when non-critical errors occur (eviction, TTL updates)
- Fail fast on critical errors (predictions, prefetch)

## Files Modified

### `ai-engine/ai/predictor.py`
- Added timezone import
- Normalized all datetime objects to UTC
- Added timezone checks before comparisons
- Added error handling around time calculations

### `ai-engine/ai/schemas.py`
- Added timezone import
- Fixed `decision_timestamp` default factory to use timezone-aware datetime

### `ai-engine/ai/main.py`
- Added comprehensive exception logging
- Added payload size logging
- Added file/line number logging
- Added structured error responses
- Fixed policy initialization threshold

## Verification

After fixes, test with:
```bash
curl -X POST http://localhost:8001/decide \
  -H "Content-Type: application/json" \
  -d @ai_test.json
```

Should return 200 OK with no datetime comparison errors.

## Key Changes Summary

1. **All datetimes are now timezone-aware (UTC)**
2. **All datetime comparisons are safe**
3. **Comprehensive error logging with stack traces**
4. **Structured error responses**
5. **No silent failures**

