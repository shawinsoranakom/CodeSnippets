async def test_successful_run_with_output_type_debug(client, simple_api_test, created_api_key):
    # This one should return outputs for all components
    # Let's just check the amount of outputs(there should be 7)
    headers = {"x-api-key": created_api_key.api_key}
    flow_id = simple_api_test["id"]
    payload = {
        "output_type": "debug",
    }
    response = await client.post(f"/api/v1/run/{flow_id}", headers=headers, json=payload)
    assert response.status_code == status.HTTP_200_OK, response.text
    # Add more assertions here to validate the response content
    json_response = response.json()
    assert "session_id" in json_response
    assert "outputs" in json_response
    outer_outputs = json_response["outputs"]
    assert len(outer_outputs) == 1
    outputs_dict = outer_outputs[0]
    assert len(outputs_dict) == 2
    assert "inputs" in outputs_dict
    assert "outputs" in outputs_dict
    assert isinstance(outputs_dict.get("outputs"), list)
    assert len(outputs_dict.get("outputs")) == 3