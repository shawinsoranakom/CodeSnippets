def store_outputs(
        self,
        dst: tuple[ir.Buffer],
        src: tuple[ir.IRNode],
        orig_src: tuple[ir.IRNode] | None = None,
        epilogue_nodes: list[ir.IRNode] | None = None,
        offsets: list[Any] | None = None,
        reindexers: list[Callable[[list[Any]], list[Any]] | None] | None = None,
        multi_output_buffers: tuple[ir.MultiOutput, ...] | None = None,
    ):
        assert isinstance(dst, Iterable)
        assert all(_dst.get_size() == _src.get_size() for _src, _dst in zip(src, dst))
        if offsets:
            offsets = parse_expr_with_index_symbols(offsets)
        gemm_num = len(src)
        final_offsets = []
        output_names = []
        if epilogue_nodes:
            if not reindexers:
                reindexers = [None] * len(epilogue_nodes)
            with LocalBufferContext(self.args) as scope:
                assert orig_src is not None
                localize_epilogue_nodes = []
                all_read_names = []
                for epilogue in epilogue_nodes:
                    all_read_names.extend(list(epilogue.get_read_names()))
                localize_epilogue_nodes.extend(scope.localize_nodes(epilogue_nodes))
                final_offsets.extend([offsets] * len(localize_epilogue_nodes))
                output_names.extend(
                    [node.get_name() for node in localize_epilogue_nodes]
                )
                for gemm_idx in range(gemm_num):
                    if orig_src[gemm_idx].get_name() != src[gemm_idx].get_name():
                        if orig_src[gemm_idx].get_name() in all_read_names or (
                            multi_output_buffers
                            and multi_output_buffers[gemm_idx].get_name()
                            in all_read_names
                        ):
                            # If any of the Epilogue nodes use this GEMM output, let's localize the GEMM output
                            global_buffers = [orig_src[gemm_idx]]
                            if (
                                multi_output_buffers
                                and multi_output_buffers[gemm_idx].get_name()
                                in all_read_names
                                and orig_src[gemm_idx].get_name() not in all_read_names
                            ):
                                # Epilogue might directly read the MultiOutput, Locallize MultiOutput to the local Buffer
                                # if this MultiOutput has not been stored by in-template epilogue
                                # otherwise, use the cse store cache if it will be stored before used
                                global_buffers.append(multi_output_buffers[gemm_idx])
                            scope.add_local_buffer(
                                src[gemm_idx],
                                global_buffers,
                            )
                        else:
                            scope.add_local_buffer(src[gemm_idx])
                            localize_epilogue_nodes.extend(
                                [L.copy(dst[gemm_idx], src[gemm_idx]).data.data]
                            )
                            reindexers.append(None)
                            output_names.append(dst[gemm_idx].get_name())
                            final_offsets.append(
                                [sympy.S.Zero] * len(dst[gemm_idx].get_size())
                            )
                res = self.store_grouped_gemm_pointwise_nodes(
                    dst,
                    localize_epilogue_nodes,
                    final_offsets,
                    reindexers,
                    output_names=output_names,
                )
                for gemm_idx in range(gemm_num):
                    if (
                        multi_output_buffers
                        and multi_output_buffers[gemm_idx].get_name() in all_read_names
                    ):
                        # If the MultiOutput is used in the Epilogue, let's remove it from args
                        multi_output_name = multi_output_buffers[gemm_idx].get_name()
                        if (
                            multi_output_name in self.args.output_buffers
                            and self.args.output_buffers[multi_output_name]
                            is not REMOVED
                        ):
                            self.remove_buffer(multi_output_name)
                return res
        else:
            if dst[0].get_name() != src[0].get_name():
                copy_list = []
                with LocalBufferContext(self.args) as scope:
                    for _src, _dst in zip(src, dst):
                        copy_list.extend([L.copy(_dst, _src).data.data])
                        scope.add_local_buffer(_src)
                        output_names.append(_dst.get_name())
                        final_offsets.append([sympy.S.Zero] * len(_dst.get_size()))
                    reindexers = [None] * len(copy_list)
                    return self.store_grouped_gemm_pointwise_nodes(
                        dst,
                        nodes=copy_list,
                        offsets=final_offsets,
                        reindexers=reindexers,
                        output_names=output_names,
                    )
            else:
                assert all(
                    _src.get_name() == _dst.get_name() for _src, _dst in zip(src, dst)
                )
                assert all(
                    _src.get_layout() == _dst.get_layout()
                    for _src, _dst in zip(src, dst)
                )
                return ""