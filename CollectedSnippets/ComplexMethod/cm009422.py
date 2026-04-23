def _complete_llm_run(self, response: LLMResult, run_id: UUID) -> Run:
        llm_run = self._get_run(run_id, run_type={"llm", "chat_model"})
        if getattr(llm_run, "outputs", None) is None:
            llm_run.outputs = {}
        else:
            llm_run.outputs = cast("dict[str, Any]", llm_run.outputs)
        if not llm_run.extra.get("__omit_auto_outputs", False):
            llm_run.outputs.update(response.model_dump())
        for i, generations in enumerate(response.generations):
            for j, generation in enumerate(generations):
                output_generation = llm_run.outputs["generations"][i][j]
                if "message" in output_generation:
                    output_generation["message"] = dumpd(
                        cast("ChatGeneration", generation).message
                    )
        llm_run.end_time = datetime.now(timezone.utc)
        llm_run.events.append({"name": "end", "time": llm_run.end_time})

        tool_call_count = 0
        for generations in response.generations:
            for generation in generations:
                if hasattr(generation, "message"):
                    msg = generation.message
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tool_call_count += len(msg.tool_calls)
        if tool_call_count > 0:
            llm_run.extra["tool_call_count"] = tool_call_count

        return llm_run