async def process(
        self, context: PipelineContext, next_func: Callable[[], Awaitable[None]]
    ) -> None:
        try:
            assert context.extracted_params is not None

            # Select models (handles video mode internally)
            model_selector = ModelSelectionStage(context.throw_error)
            context.variant_models = await model_selector.select_models(
                generation_type=context.extracted_params.generation_type,
                input_mode=context.extracted_params.input_mode,
                openai_api_key=context.extracted_params.openai_api_key,
                anthropic_api_key=context.extracted_params.anthropic_api_key,
                gemini_api_key=context.extracted_params.gemini_api_key,
            )
            if IS_DEBUG_ENABLED:
                await context.send_message(
                    "variantModels",
                    None,
                    0,
                    {"models": [model.value for model in context.variant_models]},
                    None,
                )

            generation_stage = AgenticGenerationStage(
                send_message=context.send_message,
                openai_api_key=context.extracted_params.openai_api_key,
                openai_base_url=context.extracted_params.openai_base_url,
                anthropic_api_key=context.extracted_params.anthropic_api_key,
                gemini_api_key=context.extracted_params.gemini_api_key,
                should_generate_images=context.extracted_params.should_generate_images,
                file_state=context.extracted_params.file_state,
                option_codes=context.extracted_params.option_codes,
            )

            context.variant_completions = await generation_stage.process_variants(
                variant_models=context.variant_models,
                prompt_messages=context.prompt_messages,
            )

            # Check if all variants failed
            if len(context.variant_completions) == 0:
                await context.throw_error(
                    "Error generating code. Please contact support."
                )
                return  # Don't continue the pipeline

            # Convert to list format
            context.completions = []
            for i in range(len(context.variant_models)):
                if i in context.variant_completions:
                    context.completions.append(context.variant_completions[i])
                else:
                    context.completions.append("")

        except Exception as e:
            print(f"[GENERATE_CODE] Unexpected error: {e}")
            await context.throw_error(f"An unexpected error occurred: {str(e)}")
            return  # Don't continue the pipeline

        await next_func()