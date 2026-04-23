def _get_cause(self, exception: BaseException) -> BaseException | None:
        # deprecated: description='remove support for orig_exc (deprecated in 2.23)' core_version='2.27'

        cause = super()._get_cause(exception)

        from ansible.errors import AnsibleError

        if not isinstance(exception, AnsibleError):
            return cause

        try:
            from ansible.utils.display import _display
        except Exception:  # pylint: disable=broad-except  # if config is broken, this can raise things other than ImportError
            _display = None

        if cause:
            if exception.orig_exc and exception.orig_exc is not cause and _display:
                _display.warning(
                    msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given, but differed from the cause given by `raise ... from`.",
                )

            return cause

        if exception.orig_exc:
            if _display:
                # encourage the use of `raise ... from` before deprecating `orig_exc`
                _display.warning(
                    msg=f"The `orig_exc` argument to `{type(exception).__name__}` was given without using `raise ... from orig_exc`.",
                )

            return exception.orig_exc

        return None