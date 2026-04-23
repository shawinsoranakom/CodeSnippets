def write_fetcher_unit_tests() -> None:
    """Write the fetcher unit tests to the provider test folders."""
    provider_interface = ProviderInterface()
    provider_interface_map = provider_interface.map

    fetchers = get_provider_fetchers()
    provider_fetchers: dict[str, dict[str, str]] = {}

    for provider, fetcher_dict in fetchers.items():
        path = PROVIDERS_PATH / provider / "tests" / f"test_{provider}_fetchers.py"
        generate_fetcher_unit_tests(path)

        for model_name, fetcher in fetcher_dict.items():
            fetcher_loaded = fetcher()
            fetcher_path = fetcher_loaded.__module__
            fetcher_name = fetcher_loaded.__class__.__name__

            if model_name not in provider_fetchers:
                provider_fetchers[model_name] = {}
            provider_fetchers[model_name][fetcher_name] = path

            pattern = f"from {fetcher_path}"
            if not check_pattern_in_file(path, pattern):
                with open(path, "a", encoding="utf-8", newline="\n") as f:
                    f.write(f"{pattern} import {fetcher_name}\n")

        pattern = "vcr_config"
        if not check_pattern_in_file(path, pattern):
            write_test_credentials(path, provider)

    test_template = """
@pytest.mark.record_http
def test_{fetcher_name_snake}(credentials=test_credentials):
    params = {params}

    fetcher = {fetcher_name}()
    result = fetcher.test(params, credentials)
    assert result is None
"""

    for model_name, fetcher_dict in provider_fetchers.items():
        for fetcher_name, path in fetcher_dict.items():
            pattern = f"{fetcher_name}()"
            if check_pattern_in_file(path, pattern):
                continue

            # Add logic here to grab the necessary standardized params and credentials
            test_params = get_test_params(
                param_fields=provider_interface_map[model_name]["openbb"][
                    "QueryParams"
                ]["fields"]
            )

            if "currency" in fetcher_name.lower() and "symbol" in test_params:
                test_params["symbol"] = "EUR/USD"
            if "crypto" in fetcher_name.lower() and "symbol" in test_params:
                test_params["symbol"] = "BTC/USD"
            if "indices" in fetcher_name.lower() and "symbol" in test_params:
                test_params["symbol"] = "DJI"
            if "future" in fetcher_name.lower() and "symbol" in test_params:
                test_params["symbol"] = "ES"
            if (
                "european" in fetcher_name.lower()
                and "symbol" in test_params
                and "index" in fetcher_name.lower()
            ):
                test_params["symbol"] = "BUKBUS"
            if "european" in fetcher_name.lower() and "symbol" in test_params:
                test_params["symbol"] = "BUKBUS"

            with open(path, "a", encoding="utf-8", newline="\n") as f:
                test_code = test_template.format(
                    fetcher_name_snake=to_snake_case(fetcher_name),
                    fetcher_name=fetcher_name,
                    params=test_params,
                    credentials={},
                )
                f.write(test_code)
                f.write("\n\n")