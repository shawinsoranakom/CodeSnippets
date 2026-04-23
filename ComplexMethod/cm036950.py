def _get_running_metrics_from_api(server: RemoteOpenAIServer):
    """Return (running_count, waiting_count, kv_cache_usage)"""

    response = requests.get(server.url_for("metrics"))
    assert response.status_code == HTTPStatus.OK

    # Verify running and waiting requests counts and KV cache usage are zero
    running_requests, waiting_requests, kv_cache_usage = None, None, None

    kv_cache_usage_metric = "vllm:kv_cache_usage_perc"

    for family in text_string_to_metric_families(response.text):
        if family.name == "vllm:num_requests_running":
            for sample in family.samples:
                if sample.name == "vllm:num_requests_running":
                    running_requests = sample.value
                    break
        elif family.name == "vllm:num_requests_waiting":
            for sample in family.samples:
                if sample.name == "vllm:num_requests_waiting":
                    waiting_requests = sample.value
                    break
        elif family.name == kv_cache_usage_metric:
            for sample in family.samples:
                if sample.name == kv_cache_usage_metric:
                    kv_cache_usage = sample.value
                    break

    assert running_requests is not None
    assert waiting_requests is not None
    assert kv_cache_usage is not None

    return running_requests, waiting_requests, kv_cache_usage