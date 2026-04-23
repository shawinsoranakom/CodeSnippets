async def test_openapi_schema_generation(test_client):
    """Test that the OpenAPI schema can be generated without errors.

    This test ensures that the FastAPI app can generate a valid OpenAPI schema,
    which is important for API documentation and client generation.
    """
    # Get the OpenAPI schema from the /openapi.json endpoint
    response = test_client.get('/openapi.json')

    # Check that the response is successful
    assert response.status_code == 200

    # Verify that the response is valid JSON
    schema = response.json()

    # Basic validation of the schema structure
    assert 'openapi' in schema
    assert 'info' in schema
    assert 'paths' in schema

    # Verify that the schema can be serialized to JSON without errors
    # This is a good test for ensuring all types can be properly converted to JSON Schema
    json_str = json.dumps(schema)
    assert json_str is not None

    # Optionally, you can check for specific endpoints if needed
    assert '/api/v1/settings' in schema['paths']
    assert '/health' in schema['paths']