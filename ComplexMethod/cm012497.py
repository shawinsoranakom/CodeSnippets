def store_output(
        self,
        dst: ir.Buffer,
        src: ir.Buffer,
        orig_src: ir.Buffer | None = None,
        epilogue_nodes: list[ir.IRNode] | None = None,
        offsets: list[Any] | None = None,
        reindexers: list[Callable[[list[Any]], list[Any]] | None] | None = None,
    ):
        """
        Store the `src` buffer to the `dst` buffer. The size of `src` and `dst` should match.
        If `epilogue_nodes` is provided, the `src` buffer is firstly computed with the epilogues
        before stored to `dst`. The `epilogues_nodes` are all pointwise.

        Notes:
        1. `src` and `dst` buffer could be the same buffer in which case we are doing in-place compute
           and stores. In case `epilogue_nodes` are not provided, we do nothing.
        2. The `epilogue_nodes`, if exist, have computations on `src` before storing to `dst` but since
           they come form the original Inductor IR, they might need to be adjusted before working with
           `src` and `dst` as outlined below:
           a) `src` or `dst` buffer could be a sub-slice of the ranges the `epilogue_nodes`work on.
              In this case, the `offsets` could be provided to adjust the indices passed to
              `epilogue_nodes` during codegen and the data ranges are also configured according to
              the sizes of `src` and `dst`.
           b) `dst` might be indexed in a different way as the `epilogue_nodes`, hence a `reindexer` is
              needed on the indices to `epilogue_nodes` to match the indexing of `dst`.
           c) If `src` is local, we need to add a local buffer for it and localize the `orig_src` buffer
              in `epilogue_nodes` with `src`.
        """
        assert isinstance(dst, (ir.Buffer, ir.ReinterpretView))
        assert dst.get_size() == src.get_size(), f"{dst=}, {src=}"
        if offsets:
            offsets = parse_expr_with_index_symbols(offsets)
        if epilogue_nodes:
            with LocalBufferContext(self.args) as scope:
                assert orig_src is not None
                if orig_src.get_name() != src.get_name():
                    scope.add_local_buffer(
                        src,
                        [
                            orig_src,
                        ],
                    )
                    epilogue_nodes = scope.localize_nodes(epilogue_nodes)
                return self.store_pointwise_nodes(
                    dst,
                    epilogue_nodes,  # type: ignore[arg-type]
                    offsets,
                    reindexers,
                )
        else:
            if dst.get_name() != src.get_name():
                # src is local
                copy = L.copy(dst, src).data.data
                with LocalBufferContext(self.args) as scope:
                    scope.add_local_buffer(src)

                    return self.store_pointwise_nodes(dst, [copy])
            else:
                assert dst.layout == src.layout, f"{dst=}, {src=}"
                return ""