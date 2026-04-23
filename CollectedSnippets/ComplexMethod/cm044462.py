def warmup_plugin(plugin: ExtractPlugin,  # noqa[C901]
                  batch_size: int,
                  channels_last: bool | None = None) -> bool | None:
    """Warm up a plugin that contains torch modules. If channels_last is ``None`` then attempt to
    send a channels first batch through. If it fails, send a channels last batch through

    Parameters
    ----------
    plugin
        The plugin to warmup
    batch_size
        The batch size to put through the model
    channels_last
        The expected channel order of the plugin or ``None`` to detect

    Returns
    -------
    bool
        ``True`` if the plugin is detected as channels last, ``False`` for channels first, ``None``
        for could not be detected
    """
    cv2_loglevel = None
    cv2_setlevel = None
    if channels_last is None:
        # cv2 outputs scary warnings when we are testing channels first/last with cv2-dnn plugins
        # so disable logging
        try:  # cv2 arbitrarily moves this based on build options :/
            cv2_loglevel = cv2.getLogLevel()  # type:ignore[attr-defined]
            cv2_setlevel = getattr(cv2, "setLogLevel")
        except AttributeError:
            try:
                cv2_loglevel = cv2.utils.logging.getLogLevel()  # type:ignore[attr-defined]
                cv2_setlevel = getattr(cv2.utils.logging, "setLogLevel")
            except AttributeError:
                pass

    chan_list = [False, True] if channels_last is None else [channels_last]
    is_chan_last = None

    if cv2_setlevel is not None:
        cv2_setlevel(0)

    for chan_last in chan_list:
        try:
            inp = random_input_from_plugin(plugin, batch_size, chan_last)
            plugin.process(inp)
            is_chan_last = chan_last
            break
        except Exception as err:  # pylint:disable=broad-except
            logger.debug("Exception with channels_last=%s: %s", chan_last, str(err).strip())

    if cv2_setlevel is not None:
        cv2_setlevel(cv2_loglevel)
    logger.debug("[%s] Warmed up. channels_last: %s", plugin.name, is_chan_last)
    return is_chan_last