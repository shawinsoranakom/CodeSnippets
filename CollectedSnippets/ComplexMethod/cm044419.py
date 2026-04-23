def handle_deprecated_cli_opts(arguments: Namespace,
                               additional: dict[str, tuple[str | bool | T.Any, ...]] | None = None
                               ) -> Namespace:
    """Handle deprecated command line arguments and update to correct argument.

    Deprecated cli opts will be provided in the following format:
    `"depr_<option_key>_<deprecated_opt>_<new_opt>"`

    Parameters
    ----------
    arguments
        The passed in faceswap cli arguments
    additional
        Additional information in format {deprecated_argument: (additional_text, should_update,
        [new_value])} where deprecated_argument is the command line argument, additional_text is
        any additional text to display, should_update is whether the deprecated argument should be
        replaced with the new argument and new_value is an optional value that can be passed in
        that the new argument should be set to.
        Default: ``None`` (no additional information)

    Returns
    -------
    The cli arguments with deprecated values mapped to the correct entry
    """
    logger = logging.getLogger(__name__)
    additional = {} if additional is None else additional
    for key, selected in vars(arguments).items():
        if not key.startswith("depr_") or key.startswith("depr_") and selected is None:
            continue  # Not a deprecated opt
        if isinstance(selected, bool) and not selected:
            continue  # store-true opt with default value

        opt, old, new = key.replace("depr_", "").rsplit("_", maxsplit=2)

        if opt == "removed":
            deprecation_warning(f"Command line option '-{old}' ('--{new}')",
                                "This option no longer performs any action")
            continue

        opt_additional = additional.get(old, ("", True))
        add_msg = opt_additional[0]
        should_update = opt_additional[1]
        assert isinstance(add_msg, str)
        assert isinstance(should_update, bool)
        value = selected if len(opt_additional) < 3 else opt_additional[2]

        add_msg = f" {add_msg}" if add_msg else ""
        msg = f"Use '-{new}, --{opt}' instead{add_msg}"
        deprecation_warning(f"Command line option '-{old}'", msg)

        opt = opt.replace("-", "_")
        exist = getattr(arguments, opt)
        if not should_update:
            logger.debug("Keeping existing '%s' value '%s' from additional dict", opt, exist)
        elif exist == value:
            logger.debug("Keeping existing '%s' value of %s", opt, repr(exist))
        else:
            log_at_level = logger.info if old in additional else logger.debug
            log_at_level("Updating arg '%s' from %s to %s from deprecated option '-%s'",
                         opt, repr(exist), repr(value), old)
            setattr(arguments, opt, value)

    return arguments