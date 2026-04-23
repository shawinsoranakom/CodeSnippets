async def async_chat_streamly(self, system: str, history: list, gen_conf: dict = {}, **kwargs):
        total_tokens = 0
        ans = ""
        _bundle_is_tools = self.is_tools
        _mdl_is_tools = getattr(self.mdl, "is_tools", False)
        _has_with_tools = hasattr(self.mdl, "async_chat_streamly_with_tools")
        if _bundle_is_tools and _mdl_is_tools and _has_with_tools:
            stream_fn = getattr(self.mdl, "async_chat_streamly_with_tools", None)
        elif hasattr(self.mdl, "async_chat_streamly"):
            stream_fn = getattr(self.mdl, "async_chat_streamly", None)
        else:
            raise RuntimeError(f"Model {self.mdl} does not implement async_chat or async_chat_with_tools")

        generation = None
        if self.langfuse:
            generation = self.langfuse.start_generation(trace_context=self.trace_context, name="chat_streamly", model=self.model_config["llm_name"], input={"system": system, "history": history})

        if stream_fn:
            chat_partial = partial(stream_fn, system, history, gen_conf)
            use_kwargs = self._clean_param(chat_partial, **kwargs)
            try:
                async for txt in chat_partial(**use_kwargs):
                    if isinstance(txt, int):
                        total_tokens = txt
                        break

                    if txt.endswith("</think>") and ans.endswith("</think>"):
                        ans = ans[: -len("</think>")]

                    if not self.verbose_tool_use:
                        txt = re.sub(r"<tool_call>.*?</tool_call>", "", txt, flags=re.DOTALL)

                    ans += txt
                    yield ans
            except Exception as e:
                if generation:
                    generation.update(output={"error": str(e)})
                    generation.end()
                raise
            if total_tokens and not TenantLLMService.increase_usage_by_id(self.model_config["id"], total_tokens):
                logging.error("LLMBundle.async_chat_streamly can't update token usage for {}/CHAT llm_name: {}, used_tokens: {}".format(self.tenant_id, self.model_config["llm_name"], total_tokens))
            if generation:
                generation.update(output={"output": ans}, usage_details={"total_tokens": total_tokens})
                generation.end()
            return