def _pre_process_cohere_online(self, ctx: PoolingServeContext) -> None:
        """Convert a ``CohereEmbedRequest`` into engine prompts.

        If a model has a chat template the task instruction are rendered
        as a system prompt. Otherwise they are just prepended to the input text.

        Images and mixed inputs are always batch-rendered through the chat
        template in one ``render_chat`` call.
        """
        request = ctx.request
        assert isinstance(request, CohereEmbedRequest)

        if request.texts is None and request.images is None and request.inputs is None:
            raise ValueError("One of texts, images, or inputs must be provided")

        truncate_prompt_tokens, truncation_side = self._resolve_cohere_truncation(
            request
        )
        input_type = request.input_type
        self._validate_input_type(input_type)

        if request.images is not None:
            input: list[CohereEmbedInput] = [
                CohereEmbedInput(
                    content=[
                        CohereEmbedContent(type="image_url", image_url={"url": uri})
                    ]
                )
                for uri in request.images
            ]
        elif request.inputs is not None:
            input = request.inputs
        else:
            texts = request.texts or []
            task_prefix = self._get_task_instruction_prefix(input_type)

            if task_prefix is None:
                ctx.engine_inputs = self._preprocess_cohere_text_completion(
                    request,
                    texts,
                    truncate_prompt_tokens,
                    truncation_side,
                )
                return

            all_messages = [
                self._mixed_input_to_messages(
                    CohereEmbedInput(
                        content=[CohereEmbedContent(type="text", text=text)]
                    ),
                    task_prefix=task_prefix,
                )
                for text in texts
            ]
            if self._has_chat_template():
                ctx.engine_inputs = self._batch_render_chat(
                    request,
                    all_messages,
                    truncate_prompt_tokens,
                    truncation_side,
                )
            else:
                ctx.engine_inputs = self._preprocess_cohere_text_completion(
                    request,
                    self._apply_task_instruction(texts, input_type),
                    truncate_prompt_tokens,
                    truncation_side,
                )
            return

        task_prefix = self._get_task_instruction_prefix(input_type)
        all_messages = [
            self._mixed_input_to_messages(inp, task_prefix=task_prefix) for inp in input
        ]
        ctx.engine_inputs = self._batch_render_chat(
            request, all_messages, truncate_prompt_tokens, truncation_side
        )