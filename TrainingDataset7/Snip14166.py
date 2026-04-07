def notify_file_changed(self, path):
        results = file_changed.send(sender=self, file_path=path)
        logger.debug("%s notified as changed. Signal results: %s.", path, results)
        if not any(res[1] for res in results):
            trigger_reload(path)