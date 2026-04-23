async def _stream(self, rand_cnt:str):
        s = 0
        all_content = ""
        cache = {}
        downloads = []
        for r in re.finditer(self.variable_ref_patt, rand_cnt, flags=re.DOTALL):
            if self.check_if_canceled("Message streaming"):
                return

            all_content += rand_cnt[s: r.start()]
            yield rand_cnt[s: r.start()]
            s = r.end()
            exp = r.group(1)
            if exp in cache:
                yield cache[exp]
                all_content += cache[exp]
                continue

            v = self._canvas.get_variable_value(exp)
            if v is None:
                v = ""
            if isinstance(v, partial):
                cnt = ""
                iter_obj = v()
                if inspect.isasyncgen(iter_obj):
                    async for t in iter_obj:
                        if self.check_if_canceled("Message streaming"):
                            return

                        all_content += t
                        cnt += t
                        yield t
                else:
                    for t in iter_obj:
                        if self.check_if_canceled("Message streaming"):
                            return

                        all_content += t
                        cnt += t
                        yield t
                self.set_input_value(exp, cnt)
                continue
            elif inspect.isawaitable(v):
                v = await v
            v = self._stringify_message_value(
                v, downloads=downloads, fallback_to_str=True
            )
            yield v
            self.set_input_value(exp, v)
            all_content += v
            cache[exp] = v

        if s < len(rand_cnt):
            if self.check_if_canceled("Message streaming"):
                return

            all_content += rand_cnt[s: ]
            yield rand_cnt[s: ]

        self.set_output("downloads", downloads)
        self.set_output("content", all_content)
        self._convert_content(all_content)
        await self._save_to_memory(all_content)