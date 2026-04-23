def end(
        self,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._ready:
            return
        self.trace.root_span.end(
            input=self._convert_to_langwatch_types(inputs) if self.trace.root_span.input is None else None,
            output=self._convert_to_langwatch_types(outputs) if self.trace.root_span.output is None else None,
            error=error,
        )

        if metadata and "flow_name" in metadata:
            self.trace.update(metadata=(self.trace.metadata or {}) | {"labels": [f"Flow: {metadata['flow_name']}"]})

        if self.trace.api_key or self._client._api_key:
            try:
                self.trace.__exit__(None, None, None)
            except ValueError:  # ignoring token was created in a different Context errors
                return