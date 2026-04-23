def should_delete(self):
            """Delete form if odd serial."""
            return self.instance.serial % 2 != 0