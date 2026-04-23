def handle_path_change_event(self, event: events.FileSystemEvent) -> None:
        """Handle when a path (corresponding to a file or dir) is changed.

        The events that can call this are modification, creation or moved
        events.
        """

        # Check for both modified and moved files, because many programs write
        # to a backup file then rename (i.e. move) it.
        if event.event_type == events.EVENT_TYPE_MODIFIED:
            changed_path = event.src_path
        elif event.event_type == events.EVENT_TYPE_MOVED:
            LOGGER.debug("Move event: src %s; dest %s", event.src_path, event.dest_path)
            changed_path = event.dest_path
        # On OSX with VI, on save, the file is deleted, the swap file is
        # modified and then the original file is created hence why we
        # capture EVENT_TYPE_CREATED
        elif event.event_type == events.EVENT_TYPE_CREATED:
            changed_path = event.src_path
        else:
            LOGGER.debug("Don't care about event type %s", event.event_type)
            return

        changed_path = os.path.abspath(changed_path)

        changed_path_info = self._watched_paths.get(changed_path, None)
        if changed_path_info is None:
            LOGGER.debug(
                "Ignoring changed path %s.\nWatched_paths: %s",
                changed_path,
                self._watched_paths,
            )
            return

        modification_time = util.path_modification_time(
            changed_path, changed_path_info.allow_nonexistent
        )
        if modification_time == changed_path_info.modification_time:
            LOGGER.debug("File/dir timestamp did not change: %s", changed_path)
            return

        changed_path_info.modification_time = modification_time

        new_md5 = util.calc_md5_with_blocking_retries(
            changed_path,
            glob_pattern=changed_path_info.glob_pattern,
            allow_nonexistent=changed_path_info.allow_nonexistent,
        )
        if new_md5 == changed_path_info.md5:
            LOGGER.debug("File/dir MD5 did not change: %s", changed_path)
            return

        LOGGER.debug("File/dir MD5 changed: %s", changed_path)
        changed_path_info.md5 = new_md5
        changed_path_info.on_changed.send(changed_path)