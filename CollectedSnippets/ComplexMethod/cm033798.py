def _validate_return_docs(self, returns: object, context: list[str] | None = None) -> None:
        if not isinstance(returns, dict):
            return
        if context is None:
            context = []

        for rv, data in returns.items():
            if isinstance(data, dict) and "contains" in data:
                self._validate_return_docs(data["contains"], context + [rv])

            if str(rv) in FORBIDDEN_DICTIONARY_KEYS or not str(rv).isidentifier():
                msg = f"Return value key {rv!r}"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " should not be used for return values since it cannot be accessed with dot notation in Jinja"
                self.reporter.error(
                    path=self.object_path,
                    code='bad-return-value-key',
                    msg=msg,
                )