def deprecated_setup_issue() -> None:
        os_info = get_os_info(hass)
        info = get_info(hass)
        if os_info is None or info is None:
            return
        is_haos = info.get("hassos") is not None
        board = os_info.get("board")
        arch = info.get("arch", "unknown")
        unsupported_board = board in {"tinker", "odroid-xu4", "rpi2"}
        unsupported_os_on_board = board in {"rpi3", "rpi4"}
        if is_haos and (unsupported_board or unsupported_os_on_board):
            issue_id = "deprecated_os_"
            if unsupported_os_on_board:
                issue_id += "aarch64"
            elif unsupported_board:
                issue_id += "armv7"
            ir.async_create_issue(
                hass,
                "homeassistant",
                issue_id,
                learn_more_url=DEPRECATION_URL,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key=issue_id,
                translation_placeholders={
                    "installation_guide": "https://www.home-assistant.io/installation/",
                },
            )
        bit32 = _is_32_bit()
        deprecated_architecture = bit32 and not (
            unsupported_board or unsupported_os_on_board
        )
        if not is_haos or deprecated_architecture:
            issue_id = "deprecated"
            if not is_haos:
                issue_id += "_method"
            if deprecated_architecture:
                issue_id += "_architecture"
            ir.async_create_issue(
                hass,
                "homeassistant",
                issue_id,
                learn_more_url=DEPRECATION_URL,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key=issue_id,
                translation_placeholders={
                    "installation_type": "OS" if is_haos else "Supervised",
                    "arch": arch,
                },
            )
        listener()