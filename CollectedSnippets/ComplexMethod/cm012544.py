def render(  # type: ignore[override,return,no-untyped-def]
        self,
        kernel: CppTemplateKernel,
        template_buffer_node: ir.CppTemplateBuffer | None = None,
        flag_template_buffer_has_other_users: bool | None = None,
        epilogue_nodes: list[ir.IRNode] | None = None,
        **kwargs,
    ) -> str:
        assert self.act_mapping
        act_deduplicated = get_deduplicated_act(self.act_mapping)
        wgt_start_idx = len(act_deduplicated)
        bias_start_idx = wgt_start_idx + self.gemm_grouped_num
        X_list = list(self.act_mapping.values())
        W_list = self.input_nodes[wgt_start_idx : wgt_start_idx + self.gemm_grouped_num]
        inp_list = []
        cur_idx = bias_start_idx
        for inp_idx in range(self.gemm_grouped_num):
            inp = None
            # pyrefly: ignore [bad-index, index-error]
            if self.has_bias[inp_idx]:
                inp = self.input_nodes[cur_idx]
                cur_idx += 1
            inp_list.append(inp)

        Y_list = self.output_node
        multi_output_buffers = None
        if template_buffer_node is not None:
            W_list = template_buffer_node.inputs[
                wgt_start_idx : wgt_start_idx + self.gemm_grouped_num
            ]
            assert isinstance(template_buffer_node.outputs, list)
            Y_list = template_buffer_node.outputs
            counters["inductor"]["cpp_grouped_gemm_template"] += 1
            multi_output_buffers = template_buffer_node.outputs

        template_buffer = Y_list[0]
        fake_buffers: list[ir.Buffer] = []
        Y_2d_list = Y_list
        output_dtype, compute_dtype = get_gemm_template_output_and_compute_dtype(
            X_list[0].get_dtype()
        )
        micro_gemm = create_micro_gemm(
            f"{kernel.kernel_name}_micro_gemm",
            self.m,
            self.n,
            self.k,
            input_dtype=X_list[0].get_dtype(),
            input2_dtype=W_list[0].get_dtype(),
            output_dtype=output_dtype,
            compute_dtype=compute_dtype,
            alpha=self.alpha,
            num_threads=self.num_threads,
        )
        assert micro_gemm is not None
        assert self.register_blocking == micro_gemm.register_blocking
        self.log_blockings()
        if isinstance(micro_gemm, CppMicroGemmAMX):
            counters["inductor"]["cpp_micro_gemm_amx_counter"] += 1

        L1_cache_size = torch.cpu.get_capabilities().get(
            "l1d_cache_size", 0
        )  # per core cache size in Bytes
        assert L1_cache_size > 0, f"Expect L1_cache_size > 0 but got {L1_cache_size}"

        L2_cache_size = torch.cpu.get_capabilities().get(
            "l2_cache_size", 0
        )  # per core cache size in Bytes
        assert L2_cache_size > 0, f"Expect L2_cache_size > 0 but got {L2_cache_size}"

        epilogues: list[ir.IRNode] = []
        reindexers: list[Callable[[list[Any]], list[Any]] | None] = []
        gemm_output_buffers: list[ir.Buffer] = []
        for out_buf_idx in range(self.gemm_grouped_num):
            gemm_output_name = f"{template_buffer.get_name()}_GemmOut" + str(
                out_buf_idx
            )
            gemm_output_buffers.append(
                ir.Buffer(name=gemm_output_name, layout=template_buffer.layout)
            )

        assert not self.epilogue_creator, (
            "epilogue_creator is not supported yet in Grouped GEMM Template"
        )

        kernel_args: dict[str, ir.IRNode | None] = {}
        for x_idx in range(wgt_start_idx):
            kernel_args["X" + str(x_idx)] = act_deduplicated[x_idx]
        for w_idx in range(self.gemm_grouped_num):
            kernel_args["W" + str(w_idx)] = W_list[w_idx]
        for inp_idx in range(self.gemm_grouped_num):
            kernel_args["inp" + str(inp_idx)] = inp_list[inp_idx]

        def _bias_add_epilogue(buf: ir.IRNode, inp: ir.IRNode) -> ir.Pointwise:
            return create_epilogue_with_attr(
                buf, "bias_add", other=inp, beta=self.beta, dtype=self.layout.dtype
            )

        for gemm_idx, inp in enumerate(inp_list):
            if inp:
                buffer_name = Y_list[gemm_idx].get_name()
                epilogues.append(
                    ir.ComputedBuffer(
                        name=buffer_name,
                        layout=template_buffer.layout,
                        data=_bias_add_epilogue(gemm_output_buffers[gemm_idx], inp),
                    )
                )
                reindexers.append(None)

        if epilogue_nodes:
            epilogues.extend(epilogue_nodes)
            for epilogue_node in epilogue_nodes:
                Y = cast(ir.Buffer, epilogue_node)
                _, reindexers = gen_2d_view_of_epilogue_buf(
                    Y,
                    template_buffer,
                    [
                        epilogue_node,
                    ],
                    reindexers,
                    default_reindexers=[
                        None,
                    ],
                )

        options = dict(
            N=self.n,
            K=self.k,
            PADDED_N=self.padded_n,
            aliases={},
            beta=self.beta,
            alpha=self.alpha,
            num_threads=self.num_threads,
            micro_gemm=micro_gemm,
            is_dynamic_M=self.is_dynamic_M,
            template=self,
            kernel=kernel,
            export_declaration=get_export_declaration(),
            acc_buf_dtype=torch.float,
            DTYPE_TO_CPP=DTYPE_TO_CPP,
            L1_cache_size=L1_cache_size,
            L2_cache_size=L2_cache_size,
            config=config,
            epilogue_nodes=epilogues,
            GemmOuts=gemm_output_buffers,
            reindexers=reindexers,
            kernel_args=kernel_args,
            X_list=X_list,
            W_list=W_list,
            gemm_grouped_num=self.gemm_grouped_num,
            Y_list={"Y" + str(idx): Y for idx, Y in enumerate(Y_list)},
            Y_2d_list=Y_2d_list,
            multi_output_buffers=multi_output_buffers,
            cpu_count=os.cpu_count(),
        )
        with contextlib.ExitStack() as stack:
            stack.enter_context(
                patch.object(V.graph, "get_dtype", self._fake_get_dtype(fake_buffers))
            )
            return self._template_from_string(GEMM_TEMPLATE).render(**options)