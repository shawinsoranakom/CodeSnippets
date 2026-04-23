def _get_altk_llm_object(self, *, use_output_val: bool = True) -> Any:
        """Extract the underlying LLM and map it to an ALTK client object."""
        llm_object: BaseChatModel | None = None
        steps = getattr(self.agent, "steps", None)
        if steps:
            for step in steps:
                if isinstance(step, RunnableBinding) and isinstance(step.bound, BaseChatModel):
                    llm_object = step.bound
                    break

        if isinstance(llm_object, ChatAnthropic):
            model_name = f"anthropic/{llm_object.model}"
            api_key = llm_object.anthropic_api_key.get_secret_value()
            llm_client_type = "litellm.output_val" if use_output_val else "litellm"
            llm_client = get_llm(llm_client_type)
            llm_client_obj = llm_client(model_name=model_name, api_key=api_key)
        elif isinstance(llm_object, ChatOpenAI):
            model_name = llm_object.model_name
            api_key = llm_object.openai_api_key.get_secret_value()
            llm_client_type = "openai.sync.output_val" if use_output_val else "openai.sync"
            llm_client = get_llm(llm_client_type)
            llm_client_obj = llm_client(model=model_name, api_key=api_key)
        else:
            logger.info("ALTK currently only supports OpenAI and Anthropic models through Langflow.")
            llm_client_obj = None

        return llm_client_obj