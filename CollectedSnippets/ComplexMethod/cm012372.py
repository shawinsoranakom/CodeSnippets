def recover_to_unchunked_nodes(self) -> None:
        """
        Recover the node from chunks and do the replacement.
        """
        for node in self.subgraph_output:
            meta = get_chunking_meta(node)
            assert meta is not None

            recovered: torch.fx.Node = node

            if meta.chunk_dim is not None:
                chunks = self.chunks_for_recovering[node]
                recovered = self.parent_graph.call_function(
                    aten.cat.default, (chunks, meta.chunk_dim)
                )
            elif meta.need_sum:
                recovered = self.accumulators[node]  # type: ignore[assignment]

            # do scaling last
            if meta.scale_by is not None:
                recovered = self.parent_graph.call_function(
                    aten.mul.Tensor, (recovered, meta.scale_by)
                )

            # convert back to the original dtype
            if meta.need_sum:
                original_dtype = node.meta["val"].dtype
                # TODO(shunting): do we always uses a fp32 accumulator?
                if original_dtype != torch.float32:
                    recovered = self.parent_graph.call_function(
                        prims.convert_element_type.default, (recovered, original_dtype)
                    )

            assert recovered is not node
            node.replace_all_uses_with(recovered)