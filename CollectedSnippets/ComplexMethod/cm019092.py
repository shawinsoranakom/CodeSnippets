async def _assert_log_levels(hass: HomeAssistant) -> None:
    assert logging.getLogger(UNCONFIG_NS).level == logging.NOTSET
    assert logging.getLogger(UNCONFIG_NS).isEnabledFor(logging.CRITICAL) is True
    assert (
        logging.getLogger(f"{UNCONFIG_NS}.any").isEnabledFor(logging.CRITICAL) is True
    )
    assert (
        logging.getLogger(f"{UNCONFIG_NS}.any.any").isEnabledFor(logging.CRITICAL)
        is True
    )

    assert logging.getLogger(CONFIGED_NS).isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(CONFIGED_NS).isEnabledFor(logging.WARNING) is True
    assert logging.getLogger(f"{CONFIGED_NS}.any").isEnabledFor(logging.WARNING) is True
    assert (
        logging.getLogger(f"{CONFIGED_NS}.any.any").isEnabledFor(logging.WARNING)
        is True
    )
    assert logging.getLogger(f"{CONFIGED_NS}.info").isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(f"{CONFIGED_NS}.info").isEnabledFor(logging.INFO) is True
    assert (
        logging.getLogger(f"{CONFIGED_NS}.info.any").isEnabledFor(logging.DEBUG)
        is False
    )
    assert (
        logging.getLogger(f"{CONFIGED_NS}.info.any").isEnabledFor(logging.INFO) is True
    )
    assert logging.getLogger(f"{CONFIGED_NS}.debug").isEnabledFor(logging.DEBUG) is True
    assert (
        logging.getLogger(f"{CONFIGED_NS}.debug.any").isEnabledFor(logging.DEBUG)
        is True
    )

    assert logging.getLogger(HASS_NS).isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(HASS_NS).isEnabledFor(logging.WARNING) is True

    assert logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.WARNING) is True
    assert logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.INFO) is True

    assert logging.getLogger(GROUP_NS).isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(GROUP_NS).isEnabledFor(logging.WARNING) is True
    assert logging.getLogger(GROUP_NS).isEnabledFor(logging.INFO) is True

    assert logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.WARNING) is True
    assert logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.INFO) is True

    assert logging.getLogger(ZONE_NS).isEnabledFor(logging.DEBUG) is True
    assert logging.getLogger(f"{ZONE_NS}.any").isEnabledFor(logging.DEBUG) is True

    await hass.services.async_call(
        logger.DOMAIN, "set_level", {f"{UNCONFIG_NS}.any": "debug"}, blocking=True
    )

    assert logging.getLogger(UNCONFIG_NS).level == logging.NOTSET
    assert logging.getLogger(f"{UNCONFIG_NS}.any").level == logging.DEBUG
    assert logging.getLogger(UNCONFIG_NS).level == logging.NOTSET

    await hass.services.async_call(
        logger.DOMAIN, "set_default_level", {"level": "debug"}, blocking=True
    )

    assert logging.getLogger(UNCONFIG_NS).isEnabledFor(logging.DEBUG) is True
    assert logging.getLogger(f"{UNCONFIG_NS}.any").isEnabledFor(logging.DEBUG) is True
    assert (
        logging.getLogger(f"{UNCONFIG_NS}.any.any").isEnabledFor(logging.DEBUG) is True
    )
    assert logging.getLogger("").isEnabledFor(logging.DEBUG) is True

    assert logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.DEBUG) is False
    assert logging.getLogger(GROUP_NS).isEnabledFor(logging.DEBUG) is False

    logging.getLogger(CONFIGED_NS).setLevel(logging.INFO)
    assert logging.getLogger(CONFIGED_NS).level == logging.WARNING

    logging.getLogger("").setLevel(logging.NOTSET)