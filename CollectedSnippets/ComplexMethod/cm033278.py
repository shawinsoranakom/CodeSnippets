def stream_transcription(self, audio):
        mdl = self.mdl
        supports_stream = hasattr(mdl, "stream_transcription") and callable(getattr(mdl, "stream_transcription"))
        if supports_stream:
            if self.langfuse:
                generation = self.langfuse.start_generation(
                    trace_context=self.trace_context,
                    name="stream_transcription",
                    metadata={"model": self.model_config["llm_name"]},
                )
            final_text = ""
            used_tokens = 0

            try:
                for evt in mdl.stream_transcription(audio):
                    if evt.get("event") == "final":
                        final_text = evt.get("text", "")

                    yield evt

            except Exception as e:
                err = {"event": "error", "text": str(e)}
                yield err
                final_text = final_text or ""
            finally:
                if final_text:
                    used_tokens = num_tokens_from_string(final_text)
                    TenantLLMService.increase_usage_by_id(self.model_config["id"], used_tokens)

                if self.langfuse:
                    generation.update(
                        output={"output": final_text},
                        usage_details={"total_tokens": used_tokens},
                    )
                    generation.end()

            return

        if self.langfuse:
            generation = self.langfuse.start_generation(
                trace_context=self.trace_context,
                name="stream_transcription",
                metadata={"model": self.model_config["llm_name"]},
            )

        full_text, used_tokens = mdl.transcription(audio)
        if not TenantLLMService.increase_usage_by_id(self.model_config["id"], used_tokens):
            logging.error(f"LLMBundle.stream_transcription can't update token usage for {self.tenant_id}/SEQUENCE2TXT used_tokens: {used_tokens}")

        if self.langfuse:
            generation.update(
                output={"output": full_text},
                usage_details={"total_tokens": used_tokens},
            )
            generation.end()

        yield {
            "event": "final",
            "text": full_text,
            "streaming": False,
        }