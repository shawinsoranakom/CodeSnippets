def _get_quantized_dtype_policy_by_str(policy):
    if not isinstance(policy, str):
        raise TypeError(f"`policy` must be a string. Received: policy={policy}")
    if not policy.startswith(QUANTIZATION_MODES):
        raise ValueError(
            "`policy` is incompatible with the current supported quantization."
        )
    split_name = policy.split("_from_")
    if len(split_name) != 2:
        raise ValueError(
            "Cannot convert `policy` into a valid pair (`mode`, `source_name`) "
            "to instantiate `QuantizedDTypePolicy`. "
            f"Received: policy={policy}"
        )
    mode, source_name = split_name
    if policy.startswith("int8"):
        return QuantizedDTypePolicy(mode, source_name)
    elif policy.startswith("int4"):
        # Check if mode has block_size component (e.g., "int4/128")
        if "/" in mode:
            return Int4DTypePolicy(mode, source_name)
        else:
            return QuantizedDTypePolicy(mode, source_name)
    elif policy.startswith("gptq"):
        return GPTQDTypePolicy(mode, source_name)
    elif policy.startswith("awq"):
        return AWQDTypePolicy(mode, source_name)
    elif policy.startswith("float8"):
        return QuantizedFloat8DTypePolicy(mode, source_name)
    else:
        raise NotImplementedError