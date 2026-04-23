def _cleanup(event_timestamps: dict[str, set[int]]) -> None:
            time_cutoff = (now - ORPHANED_MEDIA_AGE_CUTOFF).timestamp()
            media_path = pathlib.Path(self._media_path)
            for device_id, valid_timestamps in event_timestamps.items():
                media_files = list(media_path.glob(f"{device_id}/*"))
                _LOGGER.debug("Found %d files (device=%s)", len(media_files), device_id)
                for media_file in media_files:
                    if "-" not in media_file.name:
                        continue
                    try:
                        timestamp = int(media_file.name.split("-")[0])
                    except ValueError:
                        continue
                    if timestamp in valid_timestamps or timestamp > time_cutoff:
                        continue
                    _LOGGER.debug("Removing orphaned media file: %s", media_file)
                    try:
                        os.remove(media_file)
                    except OSError as err:
                        _LOGGER.error(
                            "Unable to remove orphaned media file: %s %s",
                            media_file,
                            err,
                        )