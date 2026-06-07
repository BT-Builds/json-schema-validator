# JSON Schema Validator API

Validate JSON data against JSON Schema without heavy libraries or slow local validation.

## Endpoints

### POST /validate
Validate data against a JSON schema.

**Headers:**
- `X-API-Key`: Required API key (use `demo-key-12345` for demo)

**Body:**
```json
{
  "schema": { "type": "string", "minLength": 5 },
  "data": "hello world"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Data is valid against schema"
}
```

### GET /health
Health check endpoint (no auth required).

## Supported Schema Types
- `object`: validates objects, supports `properties` and `required` fields
- `array`: validates arrays, supports `items` schema
- `string`: validates strings, supports `minLength`, `maxLength`, `pattern`
- `number`: validates numbers, supports `minimum`, `maximum`
- `integer`: validates integers, supports `minimum`, `maximum`
- `boolean`: validates booleans
- `null`: validates null values
- `enum`: validates any type against allowed values

## Examples

```bash
# Valid string
curl -X POST https://json-schema-validator.vercel.app/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"schema": {"type": "string"}, "data": "hello"}'

# Invalid - missing required field
curl -X POST https://json-schema-validator.vercel.app/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"schema": {"type": "object", "required": ["email"]}, "data": {"name": "John"}}'

# Integer with min/max
curl -X POST https://json-schema-validator.vercel.app/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-12345" \
  -d '{"schema": {"type": "integer", "minimum": 1, "maximum": 100}, "data": 50}'
```

## Pricing
- Free tier: 10 requests/minute
- Pro: $9/month for 1000 requests/minute

## Postman
[![Run in Postman](https://run.pstmn.io/button.svg)](https://raw.githubusercontent.com/BT-Builds/json-schema-validator/main/postman_collection.json)
