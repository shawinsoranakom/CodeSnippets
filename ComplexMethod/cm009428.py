def _patch_missing_metadata(self: LangChainTracer, run: Run) -> None:
    if not self.tracing_metadata:
        return
    metadata = run.metadata
    patched = None
    for k, v in self.tracing_metadata.items():
        # ``OVERRIDABLE_LANGSMITH_INHERITABLE_METADATA_KEYS`` are a small,
        # LangSmith-only allowlist that bypasses the "first wins" merge
        # so a nested caller (e.g. a subagent) can override a parent-set value.
        if k not in metadata or k in OVERRIDABLE_LANGSMITH_INHERITABLE_METADATA_KEYS:
            # Skip the copy when the value already matches (avoids cloning
            # the shared dict in the common "already set" case). Use a
            # ``k in metadata`` guard so a legitimate missing key whose
            # tracer value happens to be ``None`` is still patched in.
            if k in metadata and metadata[k] == v:
                continue
            if patched is None:
                # Copy on first miss to avoid mutating the shared dict.
                patched = {**metadata}
                run.extra["metadata"] = patched
            patched[k] = v