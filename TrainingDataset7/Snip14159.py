def watch_dir(self, path, glob):
        path = Path(path)
        try:
            path = path.absolute()
        except FileNotFoundError:
            logger.debug(
                "Unable to watch directory %s as it cannot be resolved.",
                path,
                exc_info=True,
            )
            return
        logger.debug("Watching dir %s with glob %s.", path, glob)
        self.directory_globs[path].add(glob)