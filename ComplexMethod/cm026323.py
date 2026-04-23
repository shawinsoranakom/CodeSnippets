def remove_files(entry: SFTPConfigEntry) -> None:
        pkey = Path(entry.data[CONF_PRIVATE_KEY_FILE])

        if pkey.exists():
            LOGGER.debug(
                "Removing private key (%s) for %s integration for host %s@%s",
                pkey,
                DOMAIN,
                entry.data[CONF_USERNAME],
                entry.data[CONF_HOST],
            )
            try:
                pkey.unlink()
            except OSError as e:
                LOGGER.warning(
                    "Failed to remove private key %s for %s integration for host %s@%s. %s",
                    pkey.name,
                    DOMAIN,
                    entry.data[CONF_USERNAME],
                    entry.data[CONF_HOST],
                    str(e),
                )

        try:
            pkey.parent.rmdir()
        except OSError as e:
            if e.errno == errno.ENOTEMPTY:  # Directory not empty
                if LOGGER.isEnabledFor(logging.DEBUG):
                    leftover_files = []
                    # If we get an exception while gathering leftover files, make sure to log plain message.
                    with contextlib.suppress(OSError):
                        leftover_files = [f.name for f in pkey.parent.iterdir()]

                    LOGGER.debug(
                        "Storage directory for %s integration is not empty (%s)%s",
                        DOMAIN,
                        str(pkey.parent),
                        f", files: {', '.join(leftover_files)}"
                        if leftover_files
                        else "",
                    )
            else:
                LOGGER.warning(
                    "Error occurred while removing directory %s for integration %s: %s at host %s@%s",
                    str(pkey.parent),
                    DOMAIN,
                    str(e),
                    entry.data[CONF_USERNAME],
                    entry.data[CONF_HOST],
                )
        else:
            LOGGER.debug(
                "Removed storage directory for %s integration",
                DOMAIN,
                entry.data[CONF_USERNAME],
                entry.data[CONF_HOST],
            )