def captureOnCommitCallbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        """Context manager to capture transaction.on_commit() callbacks."""
        callbacks = []
        start_count = len(connections[using].run_on_commit)
        try:
            yield callbacks
        finally:
            while True:
                callback_count = len(connections[using].run_on_commit)
                for _, callback, robust in connections[using].run_on_commit[
                    start_count:
                ]:
                    callbacks.append(callback)
                    if execute:
                        if robust:
                            try:
                                callback()
                            except Exception as e:
                                name = getattr(callback, "__qualname__", callback)
                                logger.exception(
                                    "Error calling %s in on_commit() (%s).",
                                    name,
                                    e,
                                )
                        else:
                            callback()

                if callback_count == len(connections[using].run_on_commit):
                    break
                start_count = callback_count