def _format(self):
        # Serialize as a set literal except when value is empty because {}
        # is an empty dict.
        return "{%s}" if self.value else "set(%s)"