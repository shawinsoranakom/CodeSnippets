def close_if_health_check_failed(self):
        """Close existing connection if it fails a health check."""
        if (
            self.connection is None
            or not self.health_check_enabled
            or self.health_check_done
        ):
            return

        if not self.is_usable():
            self.close()
        self.health_check_done = True