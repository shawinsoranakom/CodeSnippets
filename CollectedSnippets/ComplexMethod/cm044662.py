def is_terminal(self) -> bool:
        """Check if the console is writing to a terminal.

        Returns:
            bool: True if the console writing to a device capable of
                understanding escape sequences, otherwise False.
        """
        # If dev has explicitly set this value, return it
        if self._force_terminal is not None:
            return self._force_terminal

        # Fudge for Idle
        if hasattr(sys.stdin, "__module__") and sys.stdin.__module__.startswith(
            "idlelib"
        ):
            # Return False for Idle which claims to be a tty but can't handle ansi codes
            return False

        if self.is_jupyter:
            # return False for Jupyter, which may have FORCE_COLOR set
            return False

        environ = self._environ

        tty_compatible = environ.get("TTY_COMPATIBLE", "")
        # 0 indicates device is not tty compatible
        if tty_compatible == "0":
            return False
        # 1 indicates device is tty compatible
        if tty_compatible == "1":
            return True

        # https://force-color.org/
        force_color = environ.get("FORCE_COLOR")
        if force_color is not None:
            return force_color != ""

        # Any other value defaults to auto detect
        isatty: Optional[Callable[[], bool]] = getattr(self.file, "isatty", None)
        try:
            return False if isatty is None else isatty()
        except ValueError:
            # in some situation (at the end of a pytest run for example) isatty() can raise
            # ValueError: I/O operation on closed file
            # return False because we aren't in a terminal anymore
            return False