import time
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
import re

app = FastAPI(title="JSON Schema Validator API", version="1.0.0")

# Rate limiting storage (in-memory)
rate_limits: Dict[str, List[float]] = {}
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60

API_KEYS = {
    "demo": "demo-key-12345",
    "free": "free-demo-key"
}

class ValidationRequest(BaseModel):
    schema: Dict[str, Any] = Field(..., description="JSON Schema to validate against")
    data: Any = Field(..., description="Data to validate")

class ValidationResponse(BaseModel):
    valid: bool
    errors: Optional[List[str]] = None
    message: str

def check_rate_limit(api_key: str) -> bool:
    now = time.time()
    if api_key not in rate_limits:
        rate_limits[api_key] = []
    rate_limits[api_key] = [t for t in rate_limits[api_key] if now - t < RATE_LIMIT_WINDOW]
    if len(rate_limits[api_key]) >= RATE_LIMIT_REQUESTS:
        return False
    rate_limits[api_key].append(now)
    return True

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key not in API_KEYS.values():
        raise HTTPException(status_code=403, detail="Invalid API key")
    if not check_rate_limit(x_api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return x_api_key

def validate_json_schema(schema: Dict, data: Any) -> tuple[bool, List[str]]:
    errors = []
    
    try:
        schema_type = schema.get("type")
        
        if schema_type == "object":
            if not isinstance(data, dict):
                errors.append(f"Expected object, got {type(data).__name__}")
                return False, errors
            
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            for prop, prop_schema in properties.items():
                if prop in data:
                    valid, prop_errors = validate_json_schema(prop_schema, data[prop])
                    if not valid:
                        for err in prop_errors:
                            errors.append(f"{prop}.{err}")
        
        elif schema_type == "array":
            if not isinstance(data, list):
                errors.append(f"Expected array, got {type(data).__name__}")
                return False, errors
            
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    valid, item_errors = validate_json_schema(items_schema, item)
                    if not valid:
                        for err in item_errors:
                            errors.append(f"[{i}].{err}")
        
        elif schema_type == "string":
            if not isinstance(data, str):
                errors.append(f"Expected string, got {type(data).__name__}")
            else:
                min_len = schema.get("minLength")
                max_len = schema.get("maxLength")
                pattern = schema.get("pattern")
                
                if min_len and len(data) < min_len:
                    errors.append(f"String shorter than {min_len} characters")
                if max_len and len(data) > max_len:
                    errors.append(f"String longer than {max_len} characters")
                if pattern:
                    if not re.match(pattern, data):
                        errors.append(f"String does not match pattern: {pattern}")
        
        elif schema_type == "number":
            if not isinstance(data, (int, float)) or isinstance(data, bool):
                errors.append(f"Expected number, got {type(data).__name__}")
            else:
                minimum = schema.get("minimum")
                maximum = schema.get("maximum")
                
                if minimum is not None and data < minimum:
                    errors.append(f"Number {data} is less than minimum {minimum}")
                if maximum is not None and data > maximum:
                    errors.append(f"Number {data} is greater than maximum {maximum}")
        
        elif schema_type == "integer":
            if not isinstance(data, int) or isinstance(data, bool):
                errors.append(f"Expected integer, got {type(data).__name__}")
            else:
                minimum = schema.get("minimum")
                maximum = schema.get("maximum")
                
                if minimum is not None and data < minimum:
                    errors.append(f"Integer {data} is less than minimum {minimum}")
                if maximum is not None and data > maximum:
                    errors.append(f"Integer {data} is greater than maximum {maximum}")
        
        elif schema_type == "boolean":
            if not isinstance(data, bool):
                errors.append(f"Expected boolean, got {type(data).__name__}")
        
        elif schema_type == "null":
            if data is not None:
                errors.append(f"Expected null, got {type(data).__name__}")
        
        enum = schema.get("enum")
        if enum and data not in enum:
            errors.append(f"Value not in enum: {enum}")
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return len(errors) == 0, errors

@app.get("/health")
async def health():
    return {"status": "ok", "service": "json-schema-validator"}

@app.post("/validate", response_model=ValidationResponse)
async def validate(request: ValidationRequest, api_key: str = Depends(verify_api_key)):
    valid, errors = validate_json_schema(request.schema, request.data)
    
    if valid:
        return ValidationResponse(valid=True, message="Data is valid against schema")
    else:
        return ValidationResponse(valid=False, errors=errors, message="Validation failed")

@app.get("/")
async def root():
    return {"service": "JSON Schema Validator API", "version": "1.0.0", 
            "endpoints": ["/validate", "/health"], "usage": "POST /validate with JSON schema and data"}

from mangum import Mangum
handler = Mangum(app)