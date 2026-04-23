async def test_successful_run_with_input_type_any(client, simple_api_test, created_api_key):
    headers = {"x-api-key": created_api_key.api_key}
    flow_id = simple_api_test["id"]
    payload = {
        "input_type": "any",
        "output_type": "debug",
        "input_value": "value1",
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
    actual_inputs = outputs_dict.get("inputs")
    expected_inputs = {"input_value": "value1"}
    assert actual_inputs == expected_inputs, (
        f"Expected inputs to be {expected_inputs}, but got {actual_inputs}. "
        f"Full outputs_dict keys: {list(outputs_dict.keys())}, "
        f"Full response: {json_response}"
    )
    assert isinstance(outputs_dict.get("outputs"), list)
    assert len(outputs_dict.get("outputs")) == 3
    # Now we get all components that contain TextInput or ChatInput in the component_id
    any_input_outputs = [
        output
        for output in outputs_dict.get("outputs")
        if "TextInput" in output.get("component_id") or "ChatInput" in output.get("component_id")
    ]
    assert len(any_input_outputs) == 2
    # Now we check if the input_value is correct
    all_result_dicts = [output.get("results") for output in any_input_outputs]
    all_message_or_text_dicts = [
        result_dict.get("message", result_dict.get("text")) for result_dict in all_result_dicts
    ]
    assert all(message_or_text_dict.get("text") == "value1" for message_or_text_dict in all_message_or_text_dicts), (
        any_input_outputs
    )