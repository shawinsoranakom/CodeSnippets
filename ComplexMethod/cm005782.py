def test_apply_provider_config_skips_load_from_db_for_dropdown_input():
    """DropdownInput fields should NOT get load_from_db=True or the variable key as value."""
    build_config = {
        "api_key": {
            "_input_type": "SecretStrInput",
            "value": "",
            "show": False,
            "required": False,
            "advanced": False,
            "load_from_db": False,
        },
        "project_id": {
            "_input_type": "StrInput",
            "value": "",
            "show": False,
            "required": False,
            "advanced": False,
            "load_from_db": False,
        },
        "base_url_ibm_watsonx": {
            "_input_type": "DropdownInput",
            "value": "",
            "options": [
                "https://us-south.ml.cloud.ibm.com",
                "https://eu-de.ml.cloud.ibm.com",
            ],
            "show": False,
            "required": False,
            "advanced": False,
            "load_from_db": False,
        },
    }

    result = apply_provider_variable_config_to_build_config(build_config, "IBM WatsonX")

    # api_key and project_id should use load_from_db
    assert result["api_key"]["load_from_db"] is True
    assert result["api_key"]["value"] == "WATSONX_APIKEY"

    assert result["project_id"]["load_from_db"] is True
    assert result["project_id"]["value"] == "WATSONX_PROJECT_ID"

    # DropdownInput should NOT have load_from_db set
    assert result["base_url_ibm_watsonx"]["load_from_db"] is False
    # Value should remain empty (not set to "WATSONX_URL")
    assert result["base_url_ibm_watsonx"]["value"] == ""
    # But the field should still be shown
    assert result["base_url_ibm_watsonx"]["show"] is True