async def async_chat(self, system, history, gen_conf={}, **kwargs):
        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})
        gen_conf = self._clean_conf(gen_conf)

        for attempt in range(self.max_retries + 1):
            try:
                return await self._async_chat(history, gen_conf, **kwargs)
            except Exception as e:
                e = await self._exceptions_async(e, attempt)
                if e:
                    return e, 0
        assert False, "Shouldn't be here."