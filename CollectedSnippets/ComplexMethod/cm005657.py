def log_state_dict_report(
    model,
    pretrained_model_name_or_path: str,
    ignore_mismatched_sizes: bool,
    loading_info: LoadStateDictInfo,
    logger: logging.Logger | None = None,
):
    """
    Log a readable report about state_dict loading issues.

    This version is terminal-size aware: for very small terminals it falls back to a compact
    Key | Status view so output doesn't wrap badly.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Re-raise errors early if needed
    if loading_info.error_msgs:
        error_msg = "\n\t".join(loading_info.error_msgs)
        if "size mismatch" in error_msg:
            error_msg += (
                "\n\tYou may consider adding `ignore_mismatched_sizes=True` to `from_pretrained(...)` if appropriate."
            )
        raise RuntimeError(f"Error(s) in loading state_dict for {model.__class__.__name__}:\n\t{error_msg}")

    # Create the report table
    report = loading_info.create_loading_report()
    if report is None:
        return

    prelude = f"{PALETTE['bold']}{model.__class__.__name__} LOAD REPORT{PALETTE['reset']} from: {pretrained_model_name_or_path}\n"

    # Log the report as warning
    logger.warning(prelude + report)

    # Re-raise in those case, after the report
    if loading_info.conversion_errors:
        raise RuntimeError(
            "We encountered some issues during automatic conversion of the weights. For details look at the `CONVERSION` entries of "
            "the above report!"
        )
    if not ignore_mismatched_sizes and loading_info.mismatched_keys:
        raise RuntimeError(
            "You set `ignore_mismatched_sizes` to `False`, thus raising an error. For details look at the above report!"
        )