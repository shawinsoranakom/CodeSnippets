def _create_exception_message(self, e: BaseException) -> ForwardMsg:
        """Create and return an Exception ForwardMsg."""
        msg = ForwardMsg()
        exception_utils.marshall(msg.delta.new_element.exception, e)
        return msg