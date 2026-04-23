def test_lambda_cfn_run_with_empty_string_replacement_deny_list(
    deploy_cfn_template, aws_client, get_function_envars, monkeypatch
):
    """
    deploys the same lambda with an empty CFN string deny list, testing that it behaves as expected
    (i.e. the URLs in the deny list are modified)
    """
    custom_url_1 = "https://custom1.execute-api.us-east-1.amazonaws.com/test-resource"
    custom_url_2 = "https://custom2.execute-api.us-east-1.amazonaws.com/test-resource"

    monkeypatch.setattr(config, "CFN_STRING_REPLACEMENT_DENY_LIST", [])
    deployment = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__),
            "../../../templates/cfn_lambda_with_external_api_paths_in_env_vars.yaml",
        ),
        max_wait=120,
        parameters={"CustomURL": custom_url_1},
    )

    function_env_variables = get_function_envars(function_name=deployment.outputs["FunctionName"])
    # URLs that match regex to capture AWS URLs gets Localstack port appended - non-matching URLs remain unchanged.
    assert function_env_variables["API_URL_1"] == "https://api.example.com"
    assert (
        function_env_variables["API_URL_2"]
        == "https://storage.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_3"]
        == "https://reporting.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_4"]
        == "https://blockchain.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_CUSTOM"]
        == "https://custom1.execute-api.amazonaws.com:4566/test-resource"
    )

    if not is_v2_provider():
        # Not supported by the v1 provider
        return

    deployment = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__),
            "../../../templates/cfn_lambda_with_external_api_paths_in_env_vars.yaml",
        ),
        max_wait=120,
        parameters={"CustomURL": custom_url_2},
        is_update=True,
        stack_name=deployment.stack_id,
    )

    function_env_variables = get_function_envars(function_name=deployment.outputs["FunctionName"])
    # URLs that match regex to capture AWS URLs gets Localstack port appended - non-matching URLs remain unchanged.
    assert function_env_variables["API_URL_1"] == "https://api.example.com"
    assert (
        function_env_variables["API_URL_2"]
        == "https://storage.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_3"]
        == "https://reporting.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_4"]
        == "https://blockchain.execute-api.amazonaws.com:4566/test-resource"
    )
    assert (
        function_env_variables["API_URL_CUSTOM"]
        == "https://custom2.execute-api.amazonaws.com:4566/test-resource"
    )