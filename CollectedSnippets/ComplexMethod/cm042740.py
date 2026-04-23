def feed_process_params_from_cli(
    settings: BaseSettings,
    output: list[str],
    *,
    overwrite_output: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Receives feed export params (from the 'crawl' or 'runspider' commands),
    checks for inconsistencies in their quantities and returns a dictionary
    suitable to be used as the FEEDS setting.
    """
    valid_output_formats: Iterable[str] = without_none_values(
        cast("dict[str, str]", settings.getwithbase("FEED_EXPORTERS"))
    ).keys()

    def check_valid_format(output_format: str) -> None:
        if output_format not in valid_output_formats:
            raise UsageError(
                f"Unrecognized output format '{output_format}'. "
                f"Set a supported one ({tuple(valid_output_formats)}) "
                "after a colon at the end of the output URI (i.e. -o/-O "
                "<URI>:<FORMAT>) or as a file extension."
            )

    overwrite = False
    if overwrite_output:
        if output:
            raise UsageError(
                "Please use only one of -o/--output and -O/--overwrite-output"
            )
        output = overwrite_output
        overwrite = True

    result: dict[str, dict[str, Any]] = {}
    for element in output:
        try:
            feed_uri, feed_format = element.rsplit(":", 1)
            check_valid_format(feed_format)
        except (ValueError, UsageError):
            feed_uri = element
            feed_format = Path(element).suffix.replace(".", "")
        else:
            if feed_uri == "-":
                feed_uri = "stdout:"
        check_valid_format(feed_format)
        result[feed_uri] = {"format": feed_format}
        if overwrite:
            result[feed_uri]["overwrite"] = True

    # FEEDS setting should take precedence over the matching CLI options
    result.update(settings.getdict("FEEDS"))

    return result