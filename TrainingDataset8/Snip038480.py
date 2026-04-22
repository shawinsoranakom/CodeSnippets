def unhandled_exception(self) -> Optional[BaseException]:
        """The unhandled exception raised by the thread's target, if it raised one."""
        return self._unhandled_exception