def __init__(
        self,
        message: str = "",
        obj: t.Any = None,
        show_content: bool = True,
        suppress_extended_error: bool | types.EllipsisType = ...,
        orig_exc: BaseException | None = None,
        help_text: str | None = None,
    ) -> None:
        # DTFIX-FUTURE: these fallback cases mask incorrect use of AnsibleError.message, what should we do?
        if message is None:
            message = ''
        elif not isinstance(message, str):
            message = str(message)

        if self._default_message and message:
            message = _text_utils.concat_message(self._default_message, message)
        elif self._default_message:
            message = self._default_message
        elif not message:
            message = f'Unexpected {type(self).__name__} error.'

        super().__init__(message)

        self._show_content = show_content
        self._message = message
        self._help_text_value = help_text or self._default_help_text
        self.obj = obj

        # deprecated: description='deprecate support for orig_exc, callers should use `raise ... from` only' core_version='2.23'
        # deprecated: description='remove support for orig_exc' core_version='2.27'
        self.orig_exc = orig_exc

        if suppress_extended_error is not ...:
            from ..utils.display import Display

            if suppress_extended_error:
                self._show_content = False

            Display().deprecated(
                msg=f"The `suppress_extended_error` argument to `{type(self).__name__}` is deprecated.",
                version="2.23",
                help_text="Use `show_content=False` instead.",
            )