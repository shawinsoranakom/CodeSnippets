def _log_autotune_exceptions(
    exceptions: list[tuple[ChoiceCaller, BaseException]],
) -> None:
    """Log autotune exceptions to chromium event logger."""
    if not exceptions:
        return

    try:
        pt2_compile_substack = get_chromium_event_logger().get_pt2_compile_substack()
        if not pt2_compile_substack:
            return

        current_event = pt2_compile_substack[-1]
        if not current_event.endswith("_template_precompiling"):
            return

        exception_details = []
        for choice, exc in exceptions:
            try:
                choice_type = (
                    "triton" if isinstance(choice, TritonTemplateCaller) else "other"
                )
                data = {
                    "choice_type": choice_type,
                    "choice": choice.description,
                    "exception_message": str(exc),
                }

                exc_type_match = re.search(r"(\w+):", str(exc))
                if exc_type_match:
                    data["exception"] = exc_type_match.group(1)

                if "OutOfMemoryError" in str(exc):
                    required_match = re.search(r"Required: (\d+)", str(exc))
                    if required_match:
                        data["required_memory"] = required_match.group(1)

                    limit_match = re.search(r"Hardware limit:\s*(\d+)", str(exc))
                    if limit_match:
                        data["hardware_limit"] = limit_match.group(1)

                exception_details.append(data)
            except Exception:
                # Don't let logging errors break the main flow
                continue

        if exception_details:
            metadata = json.dumps({"exceptions": exception_details})
            get_chromium_event_logger().try_add_event_data(
                current_event, metadata=metadata
            )
    except Exception:
        # Silently ignore logging errors to avoid breaking autotune
        pass