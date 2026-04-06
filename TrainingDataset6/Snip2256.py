def from_shell(self, command_script):
        """Prepares command before running in app."""
        return self._expand_aliases(command_script)