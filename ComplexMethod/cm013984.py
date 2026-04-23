def get_runtime_env(self) -> GraphRuntimeEnv:
        from torch._dynamo.source import get_global_source_name

        used_globals = {}
        for (
            source
        ) in self.output_graph.export_metadata.graph_input_idx_to_local_source.values():
            global_name = get_global_source_name(source)
            if global_name is None:
                continue
            if global_name in self.f_globals:
                used_globals[global_name] = self.f_globals[global_name]

        # Scan bytecode for all external references
        external_refs = self._get_external_refs(self.bytecode)

        # Best-effort serialization of builtins referenced by the bytecode.
        # Similar to how guards prune __builtins_dict__ to only used entries.
        import builtins as _builtins

        for ref in external_refs:
            if ref not in used_globals:
                if ref.startswith("__builtins_dict__") and ref in self.f_globals:
                    used_globals[ref] = _safe_builtins_dict(self.f_globals[ref])
                elif hasattr(_builtins, ref):
                    used_globals[ref] = getattr(_builtins, ref)

        return GraphRuntimeEnv(
            bytecode=self.bytecode,
            import_sources=self.import_sources,
            used_globals=used_globals,
            closure=self.closure,
            argdefs=self.argdefs,
            kwdefaults=self.kwdefaults,
            external_refs=external_refs,
        )