def patch_rope_parameters_dict(rope_parameters: dict[str, Any]) -> None:
    if "rope_type" in rope_parameters and "type" in rope_parameters:
        rope_type = rope_parameters["rope_type"]
        rope_type_legacy = rope_parameters["type"]
        if (rope_type_legacy == "su" and rope_type == "longrope") or (
            rope_type_legacy == "mrope" and rope_type == "default"
        ):
            pass  # No action needed
        elif rope_type != rope_type_legacy:
            raise ValueError(
                f"Found conflicts between 'rope_type={rope_type}' (modern "
                f"field) and 'type={rope_type_legacy}' (legacy field). "
                "You should only specify one of them."
            )

    if "rope_type" not in rope_parameters and "type" in rope_parameters:
        rope_parameters["rope_type"] = rope_parameters["type"]
        logger.info("Replacing legacy 'type' key with 'rope_type'")

    if "rope_type" not in rope_parameters:
        raise ValueError("rope_parameters should have a 'rope_type' key")

    if rope_parameters["rope_type"] == "su":
        rope_parameters["rope_type"] = "longrope"
        logger.warning("Replacing legacy rope_type 'su' with 'longrope'")
    elif rope_parameters["rope_type"] == "mrope":
        if "mrope_section" not in rope_parameters:
            raise ValueError(
                "Legacy rope_type 'mrope' requires 'mrope_section' in rope_parameters"
            )
        rope_parameters["rope_type"] = "default"
        logger.warning("Replacing legacy rope_type 'mrope' with 'default'")