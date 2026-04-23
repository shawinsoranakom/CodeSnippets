def get_kwargs(
        self,
        script: str,
        kwargs: dict = {},
        delimiter: str = None,
        downloads: list[dict[str, Any]] | None = None,
    ) -> tuple[str, dict[str, str | list | Any]]:
        for k,v in self.get_input_elements_from_text(script).items():
            if k in kwargs:
                continue
            v = v["value"]
            if not v:
                v = ""
            ans = ""
            if isinstance(v, partial):
                iter_obj = v()
                if inspect.isasyncgen(iter_obj):
                    ans = asyncio.run(self._consume_async_gen(iter_obj))
                else:
                    for t in iter_obj:
                        ans += t
            else:
                ans = self._stringify_message_value(v, delimiter, downloads)
            if not ans:
                ans = ""
            kwargs[k] = ans
            self.set_input_value(k, ans)

        _kwargs = {}
        for n, v in kwargs.items():
            _n = re.sub("[@:.]", "_", n)
            script = re.sub(r"\{%s\}" % re.escape(n), _n, script)
            _kwargs[_n] = v
        return script, _kwargs