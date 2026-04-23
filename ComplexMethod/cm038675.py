async def create_tokenize(
        self,
        request: TokenizeRequest,
        raw_request: Request,
    ) -> TokenizeResponse | ErrorResponse:
        error_check_ret = await self._check_model(request)
        if error_check_ret is not None:
            return error_check_ret

        request_id = f"tokenize-{self._base_request_id(raw_request)}"

        lora_request = self._maybe_get_adapters(request)

        if isinstance(request, TokenizeChatRequest):
            tool_dicts = (
                None
                if request.tools is None
                else [tool.model_dump() for tool in request.tools]
            )
            error_check_ret = self.openai_serving_render.validate_chat_template(
                request_chat_template=request.chat_template,
                chat_template_kwargs=request.chat_template_kwargs,
                trust_request_chat_template=self.trust_request_chat_template,
            )
            if error_check_ret is not None:
                return error_check_ret

            _, engine_inputs = await self.openai_serving_render.preprocess_chat(
                request,
                request.messages,
                default_template=self.chat_template,
                default_template_content_format=self.chat_template_content_format,
                default_template_kwargs=self.default_chat_template_kwargs,
                tool_dicts=tool_dicts,
                skip_mm_cache=True,
            )
        else:
            engine_inputs = await self.openai_serving_render.preprocess_completion(
                request,
                prompt_input=request.prompt,
                prompt_embeds=None,
                skip_mm_cache=True,
            )

        input_ids: list[int] = []
        for engine_input in engine_inputs:
            self._log_inputs(
                request_id,
                engine_input,
                params=None,
                lora_request=lora_request,
            )

            prompt_components = self._extract_prompt_components(engine_input)
            if prompt_components.token_ids is not None:
                input_ids.extend(prompt_components.token_ids)

        token_strs = None
        if request.return_token_strs:
            tokenizer = self.renderer.get_tokenizer()
            token_strs = tokenizer.convert_ids_to_tokens(input_ids)

        return TokenizeResponse(
            tokens=input_ids,
            token_strs=token_strs,
            count=len(input_ids),
            max_model_len=self.model_config.max_model_len,
        )