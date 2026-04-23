def supports_pp(
    model: type[object] | object,
) -> bool | TypeIs[type[SupportsPP]] | TypeIs[SupportsPP]:
    supports_attributes = _supports_pp_attributes(model)
    supports_inspect = _supports_pp_inspect(model)

    if supports_attributes and not supports_inspect:
        logger.warning(
            "The model (%s) sets `supports_pp=True`, but does not accept "
            "`intermediate_tensors` in its `forward` method",
            model,
        )

    if not supports_attributes:
        pp_attrs = ("make_empty_intermediate_tensors",)
        missing_attrs = tuple(attr for attr in pp_attrs if not hasattr(model, attr))

        if getattr(model, "supports_pp", False):
            if missing_attrs:
                logger.warning(
                    "The model (%s) sets `supports_pp=True`, "
                    "but is missing PP-specific attributes: %s",
                    model,
                    missing_attrs,
                )
        else:
            if not missing_attrs:
                logger.warning(
                    "The model (%s) contains all PP-specific attributes, "
                    "but does not set `supports_pp=True`.",
                    model,
                )

    return supports_attributes and supports_inspect