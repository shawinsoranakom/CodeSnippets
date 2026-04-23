def _create_file_change_message(self) -> ForwardMsg:
        """Create and return a 'script_changed_on_disk' ForwardMsg."""
        msg = ForwardMsg()
        msg.session_event.script_changed_on_disk = True
        return msg