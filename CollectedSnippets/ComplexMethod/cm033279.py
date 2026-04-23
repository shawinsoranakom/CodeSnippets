async def async_chat(self, system: str, history: list, gen_conf: dict = {}, **kwargs):
        if self.is_tools and getattr(self.mdl, "is_tools", False) and hasattr(self.mdl, "async_chat_with_tools"):
            base_fn = self.mdl.async_chat_with_tools
        elif hasattr(self.mdl, "async_chat"):
            base_fn = self.mdl.async_chat
        else:
            raise RuntimeError(f"Model {self.mdl} does not implement async_chat or async_chat_with_tools")

        generation = None
        if self.langfuse:
            generation = self.langfuse.start_generation(trace_context=self.trace_context, name="chat", model=self.model_config["llm_name"], input={"system": system, "history": history})

        chat_partial = partial(base_fn, system, history, gen_conf)
        use_kwargs = self._clean_param(chat_partial, **kwargs)

        try:
            txt, used_tokens = await chat_partial(**use_kwargs)
        except Exception as e:
            if generation:
                generation.update(output={"error": str(e)})
                generation.end()
            raise

        txt = self._remove_reasoning_content(txt)
        if not self.verbose_tool_use:
            txt = re.sub(r"<tool_call>.*?</tool_call>", "", txt, flags=re.DOTALL)

        if used_tokens and not TenantLLMService.increase_usage_by_id(self.model_config["id"], used_tokens):
            logging.error("LLMBundle.async_chat can't update token usage for {}/CHAT llm_name: {}, used_tokens: {}".format(self.tenant_id, self.model_config["llm_name"], used_tokens))

        if generation:
            generation.update(output={"output": txt}, usage_details={"total_tokens": used_tokens})
            generation.end()

        return txt