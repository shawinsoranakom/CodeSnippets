def get_triton_kernel_and_cache_entry(node: torch.fx.Node):
    if (
        node.target
        is not torch._higher_order_ops.triton_kernel_wrap.triton_kernel_wrapper_functional
    ):
        raise AssertionError(
            f"expected triton_kernel_wrapper_functional, got {node.target}"
        )

    if not has_triton():
        raise AssertionError("triton required to serialize triton kernels")
    from triton.runtime.autotuner import Autotuner
    from triton.runtime.jit import JITFunction

    if not isinstance(node.kwargs["kernel_idx"], int):
        raise AssertionError(
            f"expected kernel_idx to be int, got {type(node.kwargs['kernel_idx'])}"
        )
    kernel = torch._higher_order_ops.triton_kernel_wrap.kernel_side_table.get_kernel(
        node.kwargs["kernel_idx"]
    )

    # For Autotuner, we need to look at the underlying JITFunction's cache
    # since the Autotuner itself doesn't have a cache
    is_autotuner = isinstance(kernel, Autotuner)
    # pyrefly: ignore [missing-attribute]
    actual_kernel = kernel.fn if is_autotuner else kernel

    if hasattr(actual_kernel, "device_caches"):
        caches = actual_kernel.device_caches
        if len(caches.keys()) != 1:
            raise AssertionError(
                f"expected exactly 1 device cache, got {len(caches.keys())}"
            )
        cache = next(iter(caches.values()))[0]
    elif hasattr(actual_kernel, "cache"):
        # old path, still used for cpu triton builds
        caches = actual_kernel.cache
        if len(caches.keys()) != 1:
            raise AssertionError(
                f"expected exactly 1 cache key, got {len(caches.keys())}"
            )
        cache = next(iter(caches.values()))
    else:
        raise AssertionError(
            # pyrefly: ignore [missing-attribute]
            f"kernel caches not found for kernel {actual_kernel.__name__}"
        )

    if len(cache.keys()) == 1:
        return actual_kernel, next(iter(cache.values()))

    has_constexprs = (
        isinstance(actual_kernel, JITFunction)
        and hasattr(actual_kernel, "constexprs")
        and len(actual_kernel.constexprs) > 0
    )

    if has_constexprs:
        constexpr_vals = {}
        # pyrefly: ignore [missing-attribute]
        for constexpr_idx in actual_kernel.constexprs:
            # pyrefly: ignore [missing-attribute]
            if constexpr_idx < len(actual_kernel.arg_names):
                # pyrefly: ignore [missing-attribute]
                param_name = actual_kernel.arg_names[constexpr_idx]
                kwargs_dict = node.kwargs.get("kwargs", {})
                if isinstance(kwargs_dict, dict):
                    if param_name in kwargs_dict:
                        constexpr_vals[param_name] = kwargs_dict[param_name]

        expected_values = [
            # pyrefly: ignore [missing-attribute]
            constexpr_vals[actual_kernel.arg_names[idx]]
            # pyrefly: ignore [missing-attribute]
            for idx in actual_kernel.constexprs
            # pyrefly: ignore [missing-attribute]
            if actual_kernel.arg_names[idx] in constexpr_vals
        ]

        # Normalize expected values for comparison with parsed constexpr values.
        # The kernel signature key stores constexprs as strings (e.g., "True", "1.5", "42"),
        # which we parse back to Python types. To ensure proper comparison, we normalize
        # the expected values: booleans, ints, and floats are kept as-is since they can
        # be compared directly with parsed values. Other types (like dtype or string
        # constants) are converted to strings to match the parsed format.
        normalized_expected = []
        for val in expected_values:
            if isinstance(val, (bool, int, float)):
                normalized_expected.append(val)
            else:
                # pyrefly: ignore [bad-argument-type]
                normalized_expected.append(str(val))

        matching_entries = []
        for sig_key, cache_entry in cache.items():
            constexpr_matches = re.findall(r"\('constexpr',\s*([^)]+)\)", sig_key)
            if constexpr_matches:
                # Parse constexpr string values back to Python types for comparison.
                # Booleans are stored as "True"/"False" strings, numbers as their string
                # representation. Values that can't be parsed as numbers are kept as strings
                # (e.g., dtype names like "torch.float32").
                constexpr_values = []
                for match in constexpr_matches:
                    if match in ("True", "False"):
                        constexpr_values.append(match == "True")
                    else:
                        try:
                            constexpr_values.append(float(match))
                        except ValueError:
                            try:
                                constexpr_values.append(int(match))
                            except ValueError:
                                constexpr_values.append(match)

                if constexpr_values == normalized_expected:
                    matching_entries.append((sig_key, cache_entry))
    else:
        matching_entries = list(cache.items())

    if len(matching_entries) == 0:
        raise AssertionError(
            # pyrefly: ignore [missing-attribute]
            f"couldn't find a kernel cache entry with metadata matching the autotuner configs for kernel {actual_kernel.__name__}. "
            f"Available cache keys: {list(cache.keys())}"
        )

    if len(matching_entries) == 1:
        return actual_kernel, matching_entries[0][1]

    if is_autotuner:
        for _sig_key, cache_entry in matching_entries:
            entry_metadata = cache_entry.metadata
            # pyrefly: ignore [missing-attribute]
            for config in kernel.configs:
                if is_metadata_matched(config, entry_metadata):
                    return actual_kernel, cache_entry

        raise AssertionError(
            # pyrefly: ignore [missing-attribute]
            f"Multiple cache entries found for autotuned kernel {actual_kernel.__name__} "
            f"{'with same constexpr values' if has_constexprs else 'with no constexpr'} "
            f"and couldn't disambiguate using configs. "
        )

    raise AssertionError(
        # pyrefly: ignore [missing-attribute]
        f"Multiple cache entries found for non-autotuned kernel {actual_kernel.__name__} "
        f"{'with same constexpr values' if has_constexprs else 'with no constexpr'}. "
        f"This should not happen. Available cache keys: {[key for key, _ in matching_entries]}"
    )