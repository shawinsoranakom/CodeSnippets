async def async_chat_with_tools(self, system: str, history: list, gen_conf: dict = {}):
        gen_conf = self._clean_conf(gen_conf)
        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})

        ans = ""
        tk_count = 0
        hist = deepcopy(history)
        for attempt in range(self.max_retries + 1):
            history = deepcopy(hist)
            try:
                for _ in range(self.max_rounds + 1):
                    logging.info(f"{self.tools=}")

                    completion_args = self._construct_completion_args(history=history, stream=False, tools=True, **gen_conf)
                    response = await litellm.acompletion(
                        **completion_args,
                        drop_params=True,
                        timeout=self.timeout,
                    )

                    tk_count += total_token_count_from_response(response)

                    if not hasattr(response, "choices") or not response.choices or not response.choices[0].message:
                        raise Exception(f"500 response structure error. Response: {response}")

                    message = response.choices[0].message

                    if not hasattr(message, "tool_calls") or not message.tool_calls:
                        _reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
                        if _reasoning:
                            ans += f"<think>{_reasoning}</think>"
                        ans += message.content or ""
                        if response.choices[0].finish_reason == "length":
                            ans = self._length_stop(ans)
                        return ans, tk_count

                    async def _exec_tool(tc):
                        name = tc.function.name
                        try:
                            args = json_repair.loads(tc.function.arguments)
                            if hasattr(self.toolcall_session, "tool_call_async"):
                                result = await self.toolcall_session.tool_call_async(name, args)
                            else:
                                result = await thread_pool_exec(self.toolcall_session.tool_call, name, args)
                            return tc, name, args, result, None
                        except Exception as e:
                            logging.exception(f"Tool call failed: {tc}")
                            return tc, name, {}, None, e

                    logging.info(f"Response tool_calls={message.tool_calls}")
                    results = await asyncio.gather(*[_exec_tool(tc) for tc in message.tool_calls])
                    history = self._append_history_batch(history, results)
                    for tc, name, args, result, err in results:
                        ans += self._verbose_tool_use(name, args, err if err else result)

                logging.warning(f"Exceed max rounds: {self.max_rounds}")
                history.append({"role": "user", "content": f"Exceed max rounds: {self.max_rounds}"})

                response, token_count = await self.async_chat("", history, gen_conf)
                ans += response
                tk_count += token_count
                return ans, tk_count

            except Exception as e:
                e = await self._exceptions_async(e, attempt)
                if e:
                    return e, tk_count

        assert False, "Shouldn't be here."