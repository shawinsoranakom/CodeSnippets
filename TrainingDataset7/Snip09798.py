def close_if_health_check_failed(self):
        if self.pool:
            # The pool only returns healthy connections.
            return
        return super().close_if_health_check_failed()