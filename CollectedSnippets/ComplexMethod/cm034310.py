def handle(self, *args: type[BaseException], skip_on_ignore: bool = False) -> t.Iterator[None]:
        """
        Handle the specified exception(s) using the defined error action.
        If `skip_on_ignore` is `True`, the body of the context manager will be skipped for `ErrorAction.IGNORE`.
        Use of `skip_on_ignore` requires enclosure within the `Skippable` context manager.
        """
        if not args:
            raise ValueError('At least one exception type is required.')

        if skip_on_ignore and self.action == ErrorAction.IGNORE:
            raise _SkipException()  # skipping ignored action

        try:
            yield
        except args as ex:
            match self.action:
                case ErrorAction.WARNING:
                    display.error_as_warning(msg=None, exception=ex)
                case ErrorAction.ERROR:
                    raise
                case _:  # ErrorAction.IGNORE
                    pass

        if skip_on_ignore:
            raise _SkipException()