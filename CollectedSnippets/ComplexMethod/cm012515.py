def _maybe_squeeze_intermediate_buffer(self, name: str, load_expr: str) -> str:
        """
        Squeeze (N,1) intermediate buffers when kernel has 1D graph inputs.

        This avoids wrong broadcasting: (N,) op (N,1) -> (N,N) instead of (N,)
        """
        if not name.startswith("buf"):
            return load_expr

        # Check if any input buffer is a 1D graph input
        has_1d_input = any(
            not buf_name.startswith("buf")
            and (buf_obj := V.graph.get_buffer(buf_name)) is not None
            and len(buf_obj.get_size()) == 1
            for buf_name in self.args.input_buffers
        )

        if has_1d_input:
            buf_obj = V.graph.get_buffer(name)
            if buf_obj is not None:
                buf_size = buf_obj.get_size()
                if len(buf_size) == 2 and buf_size[-1] == 1:
                    return f"jnp.squeeze({load_expr}, axis=-1)"

        return load_expr