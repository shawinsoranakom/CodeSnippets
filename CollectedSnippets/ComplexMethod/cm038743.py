def compute_result_filename(
    args: argparse.Namespace,
    model_id: str,
    label: str,
    current_dt: str,
) -> str | None:
    """Compute the result filename based on benchmark configuration.

    Args:
        args: Command line arguments containing result configuration
        model_id: The model identifier
        label: The benchmark label
        current_dt: Current datetime string

    Returns:
        The computed filename path or None if no result saving is requested
    """
    if not (args.plot_timeline or args.save_result or args.append_result):
        return None

    base_model_id = model_id.split("/")[-1]
    max_concurrency_str = (
        f"-concurrency{args.max_concurrency}"
        if args.max_concurrency is not None
        else ""
    )
    label = label or args.backend

    if args.ramp_up_strategy is not None:
        file_name = f"{label}-ramp-up-{args.ramp_up_strategy}-{args.ramp_up_start_rps}qps-{args.ramp_up_end_rps}qps{max_concurrency_str}-{base_model_id}-{current_dt}.json"  # noqa
    else:
        file_name = f"{label}-{args.request_rate}qps{max_concurrency_str}-{base_model_id}-{current_dt}.json"  # noqa

    if args.result_filename:
        file_name = args.result_filename

    if args.result_dir:
        os.makedirs(args.result_dir, exist_ok=True)
        file_name = os.path.join(args.result_dir, file_name)

    return file_name