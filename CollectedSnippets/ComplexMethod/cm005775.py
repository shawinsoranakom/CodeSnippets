async def test_successful_run_with_output_type_any(client, simple_api_test, created_api_key):
    # This one should have both the ChatOutput and TextOutput components
    headers = {"x-api-key": created_api_key.api_key}
    flow_id = simple_api_test["id"]
    payload = {
        "output_type": "any",
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
    assert len(outputs_dict.get("outputs")) == 1
    ids = [output.get("component_id") for output in outputs_dict.get("outputs")]
    assert all("ChatOutput" in _id or "TextOutput" in _id for _id in ids), ids
    display_names = [output.get("component_display_name") for output in outputs_dict.get("outputs")]
    assert all(name in display_names for name in ["Chat Output"]), display_names
    inner_results = [output.get("results") for output in outputs_dict.get("outputs")]
    expected_keys = ["message"]
    assert all(key in result for result in inner_results for key in expected_keys), outputs_dict