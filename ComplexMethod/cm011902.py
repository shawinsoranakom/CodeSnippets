def _log_autotune_choices_stats(
    event_name: str, timings: dict[ChoiceCaller, float]
) -> None:
    """Helper function to extract autotune metadata from benchmark results."""
    if not timings:
        return None

    metadata: dict[str, int | float | str] = {
        "num_choices": len(timings),
        "num_triton_choices": len(
            [c for c in timings if isinstance(c, TritonTemplateCaller)]
        ),
    }

    sorted_choices = sorted(timings, key=timings.__getitem__)
    best_choice = sorted_choices[0]
    metadata["best_kernel"] = best_choice.name
    if best_choice.description:
        metadata["best_kernel_desc"] = best_choice.description
    metadata["best_time"] = timings[best_choice]

    best_triton_pos = next(
        (
            i
            for i, choice in enumerate(sorted_choices)
            if isinstance(choice, TritonTemplateCaller)
        ),
        None,
    )
    if best_triton_pos is not None:
        metadata["best_triton_pos"] = best_triton_pos
        best_triton_kernel = sorted_choices[best_triton_pos]
        if best_triton_pos != 0:
            metadata["best_triton_time"] = timings[best_triton_kernel]
            metadata["best_triton_kernel"] = best_triton_kernel.name
            if best_triton_kernel.description:
                metadata["best_triton_kernel_desc"] = best_triton_kernel.description

    payload = json.dumps(metadata)
    get_chromium_event_logger().add_event_data(
        event_name, autotune_choices_stats=payload
    )
    sys.stderr.write(f"Autotune Choices Stats:\n{payload}\n")