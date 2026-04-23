def extract_request_configs(sampling_params: SamplingParams) -> dict | None:
    request_configs = None
    if (
        sampling_params.extra_args is not None
        and "kv_transfer_params" in sampling_params.extra_args
    ):
        kv_transfer_params = sampling_params.extra_args.get("kv_transfer_params")
        if kv_transfer_params is None:
            return None
        assert isinstance(kv_transfer_params, dict)
        for k, v in kv_transfer_params.items():
            if k.startswith("lmcache."):
                if request_configs is None:
                    request_configs = {}
                request_configs[k] = v
    return request_configs