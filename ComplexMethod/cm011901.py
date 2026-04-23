def _classify_kernel_operation(
    name: str, choices: list[ChoiceCaller], input_nodes
) -> str:
    """
    Classify the operation type for logging and filtering purposes.
    Returns one of: "mm", "conv", "flex", or "other"

    This is more robust than simple string matching as it:
    1. Checks template types from choices
    2. Uses input shape patterns
    3. Falls back to exact name matching (not substring)
    """
    # First, try to classify from choice types
    if choices:
        for choice in choices:
            if isinstance(choice, TritonTemplateCaller):
                # Extract template name (e.g., "mm" from "mm_1", "convolution2d" from "convolution2d_3")
                template_name = choice.name.rsplit("_", 1)[0]

                # Check known template patterns
                if template_name in (
                    "mm",
                    "bmm",
                    "mm_persistent_tma",
                    "grouped_mm",
                    "scaled_grouped_mm",
                    "mm_plus_mm",
                    "blackwell_ws_persistent_device_tma",
                    "scaled_mm_device_tma_main_loop_scaling",
                ):
                    return "mm"
                elif template_name in ("convolution2d", "convolution3d"):
                    return "conv"
                elif template_name.startswith("flex_"):
                    return "flex"

            elif isinstance(choice, ExternKernelChoice):
                # Check extern kernel names
                choice_name = choice.name
                if choice_name in (
                    "mm",
                    "bmm",
                    "addmm",
                    "baddbmm",
                    "_int_mm",
                    "_scaled_mm",
                ):
                    return "mm"
                elif "conv" in choice_name:
                    return "conv"

    # Second, use input shape heuristics for additional validation
    if len(input_nodes) >= 2:
        try:
            input_0_shape = input_nodes[0].get_size()
            input_1_shape = input_nodes[1].get_size()

            # Matrix multiplication patterns
            if len(input_0_shape) == 2 and len(input_1_shape) == 2:
                return "mm"
            elif len(input_0_shape) == 3 and len(input_1_shape) == 3:
                return "mm"  # bmm

            # Convolution patterns: input NCHW/NCDHW, weight OIHW/OIDHW
            elif len(input_0_shape) in (4, 5) and len(input_1_shape) in (4, 5):
                # Could be conv or flex_attention, prefer template name if available
                if len(input_0_shape) == 4 and len(input_1_shape) == 4:
                    # Check if it looks like conv (channel dims match)
                    # Conv: input[N,C,H,W] @ weight[O,C,kH,kW] where input[1] == weight[1]
                    try:
                        if input_0_shape[1] == input_1_shape[1]:
                            return "conv"
                    except (IndexError, TypeError):
                        pass

        except (ValueError, IndexError, AttributeError):
            pass

    # Last resort: exact name matching (not substring to avoid false positives)
    name_lower = name.lower()
    if name_lower in ("mm", "bmm", "addmm", "baddbmm"):
        return "mm"
    elif name_lower in (
        "convolution",
        "convolution2d",
        "convolution3d",
        "conv2d",
        "conv3d",
    ):
        return "conv"
    elif name_lower.startswith("flex_"):
        return "flex"

    return "other"