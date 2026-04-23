def _should_stream(
        self,
        *,
        async_api: bool,
        run_manager: CallbackManagerForLLMRun
        | AsyncCallbackManagerForLLMRun
        | None = None,
        **kwargs: Any,
    ) -> bool:
        """Determine if a given model call should hit the streaming API."""
        sync_not_implemented = type(self)._stream == BaseChatModel._stream  # noqa: SLF001
        async_not_implemented = type(self)._astream == BaseChatModel._astream  # noqa: SLF001

        # Check if streaming is implemented.
        if (not async_api) and sync_not_implemented:
            return False
        # Note, since async falls back to sync we check both here.
        if async_api and async_not_implemented and sync_not_implemented:
            return False

        # Check if streaming has been disabled on this instance.
        if self.disable_streaming is True:
            return False
        # We assume tools are passed in via "tools" kwarg in all models.
        if self.disable_streaming == "tool_calling" and kwargs.get("tools"):
            return False

        # Check if a runtime streaming flag has been passed in.
        if "stream" in kwargs:
            return bool(kwargs["stream"])

        if "streaming" in self.model_fields_set:
            streaming_value = getattr(self, "streaming", None)
            if isinstance(streaming_value, bool):
                return streaming_value

        # Check if any streaming callback handlers have been passed in.
        handlers = run_manager.handlers if run_manager else []
        return any(isinstance(h, _StreamingCallbackHandler) for h in handlers)