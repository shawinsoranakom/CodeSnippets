def _get_callback(
        self,
        *,
        spider: Spider,
        opts: argparse.Namespace,
        response: Response | None = None,
    ) -> CallbackT:
        cb: str | CallbackT | None = None
        if response:
            cb = response.meta["_callback"]
        if not cb:
            if opts.callback:
                cb = opts.callback
            elif response and opts.rules and self.first_response == response:
                cb = self.get_callback_from_rules(spider, response)
                if not cb:
                    raise ValueError(
                        f"Cannot find a rule that matches {response.url!r} in spider: "
                        f"{spider.name}"
                    )
            else:
                cb = "parse"

        if not callable(cb):
            assert cb is not None
            cb_method = getattr(spider, cb, None)
            if callable(cb_method):
                cb = cb_method
            else:
                raise ValueError(
                    f"Cannot find callback {cb!r} in spider: {spider.name}"
                )
        assert callable(cb)
        return cb