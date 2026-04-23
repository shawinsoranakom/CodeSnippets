async def test_read_variables(client: AsyncClient, generic_variable, credential_variable, logged_in_headers):
    # Create a generic variable
    create_response = await client.post("api/v1/variables/", json=generic_variable, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED

    # Create a credential variable
    create_response = await client.post("api/v1/variables/", json=credential_variable, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED

    response = await client.get("api/v1/variables/", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK

    # Check both variables exist
    assert generic_variable["name"] in [r["name"] for r in result]
    assert credential_variable["name"] in [r["name"] for r in result]

    # Assert that credentials are not decrypted and generic are decrypted
    credential_vars = [r for r in result if r["type"] == CREDENTIAL_TYPE]
    generic_vars = [r for r in result if r["type"] == GENERIC_TYPE]

    # Credential variables should remain encrypted (value should be different)
    assert all(c["value"] != credential_variable["value"] for c in credential_vars)

    # Generic variables should be decrypted (value should match original)
    assert all(g["value"] == generic_variable["value"] for g in generic_vars)