def _check_subscription(self, sub):
        subscription = self.client.getSubscription(sub)
        if not subscription:
            return
        logger.debug("Watchman subscription %s has results.", sub)
        for result in subscription:
            # When using watch-project, it's not simple to get the relative
            # directory without storing some specific state. Store the full
            # path to the directory in the subscription name, prefixed by its
            # type (glob, files).
            root_directory = Path(result["subscription"].split(":", 1)[1])
            logger.debug("Found root directory %s", root_directory)
            for file in result.get("files", []):
                self.notify_file_changed(root_directory / file)