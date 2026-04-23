def _generate(
        self,
        prompts: list[str],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        # List to hold all results
        text_generations: list[str] = []
        pipeline_kwargs = kwargs.get("pipeline_kwargs", {})
        skip_prompt = kwargs.get("skip_prompt", False)

        for i in range(0, len(prompts), self.batch_size):
            batch_prompts = prompts[i : i + self.batch_size]

            # Process batch of prompts
            responses = self.pipeline(
                batch_prompts,
                **pipeline_kwargs,
            )

            # Process each response in the batch
            for j, response in enumerate(responses):
                if isinstance(response, list):
                    # if model returns multiple generations, pick the top one
                    response = response[0]

                if (
                    self.pipeline.task == "text-generation"
                    or self.pipeline.task == "text2text-generation"
                    or self.pipeline.task == "image-text-to-text"
                ):
                    text = response["generated_text"]
                elif self.pipeline.task == "summarization":
                    text = response["summary_text"]
                elif self.pipeline.task in "translation":
                    text = response["translation_text"]
                else:
                    msg = (
                        f"Got invalid task {self.pipeline.task}, "
                        f"currently only {VALID_TASKS} are supported"
                    )
                    raise ValueError(msg)
                if skip_prompt:
                    text = text[len(batch_prompts[j]) :]
                # Append the processed text to results
                text_generations.append(text)

        return LLMResult(
            generations=[[Generation(text=text)] for text in text_generations]
        )