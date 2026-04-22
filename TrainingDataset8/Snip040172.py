def modify_mock_file():
            self.mock_util.path_modification_time = lambda *args: mod_count[0]
            self.mock_util.calc_md5_with_blocking_retries = (
                lambda _, **kwargs: "%d" % mod_count[0]
            )

            ev = events.FileSystemEvent(filename)
            ev.event_type = events.EVENT_TYPE_MODIFIED
            folder_handler.on_modified(ev)

            mod_count[0] += 1.0