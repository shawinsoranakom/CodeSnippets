def _get_sleep_metrics_from_api(response: requests.Response):
    """Return (awake, weights_offloaded, discard_all)"""

    awake, weights_offloaded, discard_all = None, None, None

    for family in text_string_to_metric_families(response.text):
        if family.name == "vllm:engine_sleep_state":
            for sample in family.samples:
                if sample.name == "vllm:engine_sleep_state":
                    for label_name, label_value in sample.labels.items():
                        if label_value == "awake":
                            awake = sample.value
                        elif label_value == "weights_offloaded":
                            weights_offloaded = sample.value
                        elif label_value == "discard_all":
                            discard_all = sample.value

    assert awake is not None
    assert weights_offloaded is not None
    assert discard_all is not None

    return awake, weights_offloaded, discard_all