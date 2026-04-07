def tick(self):
        mtimes = {}
        while True:
            for filepath, mtime in self.snapshot_files():
                old_time = mtimes.get(filepath)
                mtimes[filepath] = mtime
                if old_time is None:
                    logger.debug("File %s first seen with mtime %s", filepath, mtime)
                    continue
                elif mtime > old_time:
                    logger.debug(
                        "File %s previous mtime: %s, current mtime: %s",
                        filepath,
                        old_time,
                        mtime,
                    )
                    self.notify_file_changed(filepath)

            time.sleep(self.SLEEP_TIME)
            yield