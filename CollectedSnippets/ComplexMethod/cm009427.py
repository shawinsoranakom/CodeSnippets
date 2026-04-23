async def on_llm_end(
        self, response: LLMResult, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """End a trace for a model run.

        For both chat models and non-chat models (legacy text-completion LLMs).

        Raises:
            ValueError: If the run type is not `'llm'` or `'chat_model'`.
        """
        run_info = self.run_map.pop(run_id)
        inputs_ = run_info.get("inputs")

        generations: list[list[GenerationChunk]] | list[list[ChatGenerationChunk]]
        output: dict | BaseMessage = {}

        if run_info["run_type"] == "chat_model":
            generations = cast("list[list[ChatGenerationChunk]]", response.generations)
            for gen in generations:
                if output != {}:
                    break
                for chunk in gen:
                    output = chunk.message
                    break

            event = "on_chat_model_end"
        elif run_info["run_type"] == "llm":
            generations = cast("list[list[GenerationChunk]]", response.generations)
            output = {
                "generations": [
                    [
                        {
                            "text": chunk.text,
                            "generation_info": chunk.generation_info,
                            "type": chunk.type,
                        }
                        for chunk in gen
                    ]
                    for gen in generations
                ],
                "llm_output": response.llm_output,
            }
            event = "on_llm_end"
        else:
            msg = f"Unexpected run type: {run_info['run_type']}"
            raise ValueError(msg)

        self._send(
            {
                "event": event,
                "data": {"output": output, "input": inputs_},
                "run_id": str(run_id),
                "name": run_info["name"],
                "tags": run_info["tags"],
                "metadata": run_info["metadata"],
                "parent_ids": self._get_parent_ids(run_id),
            },
            run_info["run_type"],
        )