def do_download() -> None:
        """Download the file."""
        final_path = None
        filename = target_filename
        try:
            req = requests.get(url, stream=True, headers=headers, timeout=10)

            if req.status_code != HTTPStatus.OK:
                _LOGGER.warning(
                    "Downloading '%s' failed, status_code=%d", url, req.status_code
                )
                service.hass.bus.fire(
                    f"{DOMAIN}_{DOWNLOAD_FAILED_EVENT}",
                    {"url": url, "filename": filename},
                )

            else:
                if filename is None and "content-disposition" in req.headers:
                    if match := re.search(
                        r"filename=(\S+)", req.headers["content-disposition"]
                    ):
                        filename = match.group(1).strip("'\" ")

                if not filename:
                    filename = os.path.basename(url).strip()

                if not filename:
                    filename = "ha_download"

                # Check the filename
                raise_if_invalid_filename(filename)

                # Do we want to download to subdir, create if needed
                if subdir:
                    subdir_path = os.path.join(download_path, subdir)

                    # Ensure subdir exist
                    os.makedirs(subdir_path, exist_ok=True)

                    final_path = os.path.join(subdir_path, filename)

                else:
                    final_path = os.path.join(download_path, filename)

                path, ext = os.path.splitext(final_path)

                # If file exist append a number.
                # We test filename, filename_2..
                if not overwrite:
                    tries = 1
                    final_path = path + ext
                    while os.path.isfile(final_path):
                        tries += 1

                        final_path = f"{path}_{tries}.{ext}"

                _LOGGER.debug("%s -> %s", url, final_path)

                with open(final_path, "wb") as fil:
                    fil.writelines(req.iter_content(1024))

                _LOGGER.debug("Downloading of %s done", url)
                service.hass.bus.fire(
                    f"{DOMAIN}_{DOWNLOAD_COMPLETED_EVENT}",
                    {"url": url, "filename": filename},
                )

        except requests.exceptions.ConnectionError:
            _LOGGER.exception("ConnectionError occurred for %s", url)
            service.hass.bus.fire(
                f"{DOMAIN}_{DOWNLOAD_FAILED_EVENT}",
                {"url": url, "filename": filename},
            )

            # Remove file if we started downloading but failed
            if final_path and os.path.isfile(final_path):
                os.remove(final_path)
        except ValueError:
            _LOGGER.exception("Invalid value")
            service.hass.bus.fire(
                f"{DOMAIN}_{DOWNLOAD_FAILED_EVENT}",
                {"url": url, "filename": filename},
            )

            # Remove file if we started downloading but failed
            if final_path and os.path.isfile(final_path):
                os.remove(final_path)