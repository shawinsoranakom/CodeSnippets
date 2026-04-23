def resolve_online_quant_config(
    quantization: str | None,
    quantization_config: dict[str, Any] | OnlineQuantizationConfigArgs | None,
) -> OnlineQuantizationConfigArgs | None:
    """Resolve online quant scheme shorthand into a quantization config.

    If ``quantization`` is an online quant scheme (e.g. ``'fp8_per_tensor'``),
    ensures ``quantization_config`` has a matching ``global_scheme`` and casts
    it to :class:`OnlineQuantizationConfigArgs` if needed.
    """
    online_quant_values = {s.value for s in OnlineQuantScheme}
    valid_quantization_values = online_quant_values | {"online"}
    if quantization not in valid_quantization_values:
        if quantization_config is not None:
            raise ValueError(
                f"quantization_config is only supported when quantization "
                f"is one of {sorted(valid_quantization_values)}, "
                f"got quantization={quantization!r}"
            )
        return None

    if quantization in online_quant_values:
        scheme = OnlineQuantScheme(quantization)

        if quantization_config is None:
            quantization_config = {
                "global_scheme": scheme.value,
            }
        elif isinstance(quantization_config, OnlineQuantizationConfigArgs):
            if quantization_config.global_scheme is None:
                quantization_config.global_scheme = scheme
            elif quantization_config.global_scheme != scheme:
                raise ValueError(
                    f"quantization={quantization!r} conflicts with "
                    f"quantization_config.global_scheme="
                    f"{quantization_config.global_scheme.value!r}. "
                    f"These must match when both are specified."
                )
        elif isinstance(quantization_config, dict):
            existing = quantization_config.get("global_scheme")
            if existing is None:
                quantization_config["global_scheme"] = scheme.value
            else:
                # Coerce to enum for comparison
                existing_scheme = (
                    OnlineQuantScheme(existing)
                    if isinstance(existing, str)
                    else existing
                )
                if existing_scheme != scheme:
                    raise ValueError(
                        f"quantization={quantization!r} conflicts "
                        f"with quantization_config"
                        f"['global_scheme']={existing!r}. "
                        f"These must match when both are specified."
                    )

    # Cast dict to OnlineQuantizationConfigArgs
    if isinstance(quantization_config, dict):
        quantization_config = OnlineQuantizationConfigArgs(**quantization_config)

    return quantization_config