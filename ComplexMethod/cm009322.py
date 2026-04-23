def _stream_with_aggregation(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        verbose: bool = False,  # noqa: FBT002
        **kwargs: Any,
    ) -> GenerationChunk:
        final_chunk = None
        thinking_content = ""
        for stream_resp in self._create_generate_stream(prompt, stop, **kwargs):
            if not isinstance(stream_resp, str):
                if stream_resp.get("thinking"):
                    thinking_content += stream_resp["thinking"]
                chunk = GenerationChunk(
                    text=stream_resp.get("response", ""),
                    generation_info=(
                        dict(stream_resp) if stream_resp.get("done") is True else None
                    ),
                )
                if final_chunk is None:
                    final_chunk = chunk
                else:
                    final_chunk += chunk
                if run_manager:
                    run_manager.on_llm_new_token(
                        chunk.text,
                        chunk=chunk,
                        verbose=verbose,
                    )
        if final_chunk is None:
            msg = "No data received from Ollama stream."
            raise ValueError(msg)

        if thinking_content:
            if final_chunk.generation_info:
                final_chunk.generation_info["thinking"] = thinking_content
            else:
                final_chunk.generation_info = {"thinking": thinking_content}

        return final_chunk