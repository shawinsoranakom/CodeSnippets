async def async_chat_streamly_with_tools(self, system: str, history: list, gen_conf: dict = {}):
        gen_conf = self._clean_conf(gen_conf)
        tools = self.tools
        if system and history and history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system})

        total_tokens = 0
        hist = deepcopy(history)

        for attempt in range(self.max_retries + 1):
            history = deepcopy(hist)
            try:
                for _round in range(self.max_rounds + 1):
                    reasoning_start = False
                    logging.info(f"[ToolLoop] round={_round} model={self.model_name} tools={[t['function']['name'] for t in tools]}")

                    response = await self.async_client.chat.completions.create(model=self.model_name, messages=history, stream=True, tools=tools, tool_choice="auto", **gen_conf)

                    final_tool_calls = {}
                    answer = ""

                    async for resp in response:
                        if not hasattr(resp, "choices") or not resp.choices:
                            continue

                        delta = resp.choices[0].delta

                        if hasattr(delta, "tool_calls") and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                index = tool_call.index
                                if index not in final_tool_calls:
                                    if not tool_call.function.arguments:
                                        tool_call.function.arguments = ""
                                    final_tool_calls[index] = tool_call
                                else:
                                    final_tool_calls[index].function.arguments += tool_call.function.arguments or ""
                            continue

                        if not hasattr(delta, "content") or delta.content is None:
                            delta.content = ""

                        _reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
                        if _reasoning:
                            ans = ""
                            if not reasoning_start:
                                reasoning_start = True
                                ans = "<think>"
                            ans += _reasoning + "</think>"
                            yield ans
                        else:
                            reasoning_start = False
                            answer += delta.content
                            yield delta.content

                        tol = total_token_count_from_response(resp)
                        if not tol:
                            total_tokens += num_tokens_from_string(delta.content)
                        else:
                            total_tokens = tol

                        finish_reason = getattr(resp.choices[0], "finish_reason", "")
                        if finish_reason == "length":
                            yield self._length_stop("")

                    if answer and not final_tool_calls:
                        logging.info(f"[ToolLoop] round={_round} completed with text response, exiting")
                        yield total_tokens
                        return

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

                    tcs = list(final_tool_calls.values())
                    logging.info(f"[ToolLoop] round={_round} executing {len(tcs)} tool(s): {[tc.function.name for tc in tcs]}")
                    for tc in tcs:
                        try:
                            args = json_repair.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        yield self._verbose_tool_use(tc.function.name, args, "Begin to call...")
                    results = await asyncio.gather(*[_exec_tool(tc) for tc in tcs])
                    history = self._append_history_batch(history, results)
                    for tc, name, args, result, err in results:
                        yield self._verbose_tool_use(name, args, err if err else result)

                logging.warning(f"Exceed max rounds: {self.max_rounds}")
                history.append({"role": "user", "content": f"Exceed max rounds: {self.max_rounds}"})

                response = await self.async_client.chat.completions.create(model=self.model_name, messages=history, stream=True, tools=tools, tool_choice="auto", **gen_conf)

                async for resp in response:
                    if not hasattr(resp, "choices") or not resp.choices:
                        continue
                    delta = resp.choices[0].delta
                    if not hasattr(delta, "content") or delta.content is None:
                        continue
                    tol = total_token_count_from_response(resp)
                    if not tol:
                        total_tokens += num_tokens_from_string(delta.content)
                    else:
                        total_tokens = tol
                    yield delta.content

                yield total_tokens
                return

            except Exception as e:
                e = await self._exceptions_async(e, attempt)
                if e:
                    logging.error(f"async_chat_streamly failed: {e}")
                    yield e
                    yield total_tokens
                    return

        assert False, "Shouldn't be here."