def _maybe_preserve_original_meta(
        self, tx: "InstructionTranslatorBase", node: fx.Node
    ) -> None:
        if (
            self._orig_gm_meta
            and self._orig_gm_lineno_map
            and self._orig_gm_firstlineno
        ):
            lineno = tx.current_instruction.starts_line
            node_idx = None
            if lineno is not None:
                node_idx = self._orig_gm_lineno_map.get(
                    lineno - self._orig_gm_firstlineno, None
                )
            if node_idx is not None:
                meta = self._orig_gm_meta[node_idx]
                for field in fx.proxy._COPY_META_FIELDS:
                    if field in meta:
                        node.meta[field] = meta[field]
                if "stack_trace" in meta:
                    node.meta["stack_trace"] = meta["stack_trace"]