def copy_with_metadata_defaults(
        self,
        *,
        metadata: Mapping[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> LangChainTracer:
        """Return a new tracer with merged tracer-only defaults."""
        base_metadata = self.tracing_metadata
        if metadata is None:
            merged_metadata = dict(base_metadata) if base_metadata is not None else None
        elif base_metadata is None:
            merged_metadata = dict(metadata)
        else:
            merged_metadata = dict(base_metadata)
            for key, value in metadata.items():
                # For allowlisted LangSmith-only inheritable metadata keys
                # (e.g. ``ls_agent_type``), nested callers are allowed to
                # OVERRIDE the value inherited from an ancestor. For all
                # other keys we keep the existing "first wins" behavior so
                # that ancestor-provided tracing metadata is not accidentally
                # clobbered by child runs.
                if (
                    key not in merged_metadata
                    or key in OVERRIDABLE_LANGSMITH_INHERITABLE_METADATA_KEYS
                ):
                    merged_metadata[key] = value

        merged_tags = sorted(set(self.tags + tags)) if tags else self.tags

        return self.__class__(
            example_id=self.example_id,
            project_name=self.project_name,
            client=self.client,
            tags=merged_tags,
            metadata=merged_metadata,
            run_map=self.run_map,
            order_map=self.order_map,
            _external_run_ids=self._external_run_ids,
        )