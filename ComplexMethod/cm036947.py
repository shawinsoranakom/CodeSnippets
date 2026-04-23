async def test_metrics_counts(
    server: RemoteOpenAIServer,
    client: openai.AsyncClient,
    model_key: str,
):
    if model_key == "multimodal":
        pytest.skip("Unnecessary test")

    model_name = MODELS[model_key]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    prompt_ids = tokenizer.encode(_PROMPT)
    num_requests = 10
    max_tokens = 10

    for _ in range(num_requests):
        # sending a request triggers the metrics to be logged.
        await client.completions.create(
            model=model_name,
            prompt=prompt_ids,
            max_tokens=max_tokens,
        )

    response = requests.get(server.url_for("metrics"))
    print(response.text)
    assert response.status_code == HTTPStatus.OK

    # Loop over all expected metric_families
    expected_values = _get_expected_values(num_requests, prompt_ids, max_tokens)
    for metric_family, suffix_values_list in expected_values.items():
        if metric_family not in EXPECTED_METRICS_V1 or (
            not server.show_hidden_metrics
            and metric_family in HIDDEN_DEPRECATED_METRICS
        ):
            continue

        found_metric = False

        # Check to see if the metric_family is found in the prom endpoint.
        for family in text_string_to_metric_families(response.text):
            if family.name == metric_family:
                found_metric = True

                # Check that each suffix is found in the prom endpoint.
                for suffix, expected_value in suffix_values_list:
                    metric_name_w_suffix = f"{metric_family}{suffix}"
                    found_suffix = False

                    for sample in family.samples:
                        if sample.name == metric_name_w_suffix:
                            found_suffix = True

                            # For each suffix, value sure the value matches
                            # what we expect.
                            assert sample.value == expected_value, (
                                f"{metric_name_w_suffix} expected value of "
                                f"{expected_value} did not match found value "
                                f"{sample.value}"
                            )
                            break
                    assert found_suffix, (
                        f"Did not find {metric_name_w_suffix} in prom endpoint"
                    )
                break

        assert found_metric, f"Did not find {metric_family} in prom endpoint"