def _log_robust_failure(self, receiver, err):
        logger.error(
            "Error calling %s in Signal.send_robust() (%s)",
            receiver.__qualname__,
            err,
            exc_info=err,
        )