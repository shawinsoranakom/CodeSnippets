async def async_chat_streamly(self, system, history, gen_conf, **kwargs):
        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})
        logging.info("[HISTORY STREAMLY]" + json.dumps(history, ensure_ascii=False, indent=4))
        gen_conf = self._clean_conf(gen_conf)
        reasoning_start = False
        total_tokens = 0

        completion_args = self._construct_completion_args(history=history, stream=True, tools=False, **gen_conf)
        stop = kwargs.get("stop")
        if stop:
            completion_args["stop"] = stop

        for attempt in range(self.max_retries + 1):
            try:
                stream = await litellm.acompletion(
                    **completion_args,
                    drop_params=True,
                    timeout=self.timeout,
                )

                async for resp in stream:
                    if not hasattr(resp, "choices") or not resp.choices:
                        continue

                    delta = resp.choices[0].delta
                    if not hasattr(delta, "content") or delta.content is None:
                        delta.content = ""

                    _reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
                    if kwargs.get("with_reasoning", True) and _reasoning:
                        ans = ""
                        if not reasoning_start:
                            reasoning_start = True
                            ans = "<think>"
                        ans += _reasoning + "</think>"
                    else:
                        reasoning_start = False
                        ans = delta.content

                    tol = total_token_count_from_response(resp)
                    if not tol:
                        tol = num_tokens_from_string(delta.content)
                    total_tokens += tol

                    finish_reason = resp.choices[0].finish_reason if hasattr(resp.choices[0], "finish_reason") else ""
                    if finish_reason == "length":
                        if is_chinese(ans):
                            ans += LENGTH_NOTIFICATION_CN
                        else:
                            ans += LENGTH_NOTIFICATION_EN

                    yield ans
                yield total_tokens
                return
            except Exception as e:
                e = await self._exceptions_async(e, attempt)
                if e:
                    yield e
                    yield total_tokens
                    return