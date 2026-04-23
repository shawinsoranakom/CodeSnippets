def get_options(
        self,
        kernel: CppTemplateKernel,
        template_buffer_node: ir.CppTemplateBuffer | None = None,
        flag_template_buffer_has_other_users: bool | None = None,
        epilogue_nodes: list[ir.IRNode] | None = None,
    ) -> dict[str, Any]:
        assert len(self.input_nodes) >= 2

        int8_gemm = self.input_nodes[0].get_dtype() in [torch.uint8, torch.int8]
        x_scale = None
        x_zp = None
        w_scale = None
        w_zp = None
        inp = None
        q_group_size_node = None
        qscale_and_zeros = None
        if int8_gemm:
            X, W = self.input_nodes[0], self.input_nodes[1]
            bias_idx = 2 if self.has_bias else 1
            inp = self.input_nodes[bias_idx] if self.has_bias else None
            x_scale = self.input_nodes[bias_idx + 1]
            x_zp = self.input_nodes[bias_idx + 2]
            w_scale = self.input_nodes[bias_idx + 3]
            w_zp = self.input_nodes[bias_idx + 4]
            Y = self.output_node
        elif self.is_woq_int4():
            X, W = self.input_nodes[0], self.input_nodes[1]
            Y = self.output_node
            q_group_size_node = self.input_nodes[2]
            qscale_and_zeros = self.input_nodes[3]
        else:
            X, W = self.input_nodes[0], self.input_nodes[1]
            Y = self.output_node
            inp = self.input_nodes[2] if self.has_bias else None

        template_buffer_has_other_users = None

        if template_buffer_node is not None:
            # Use the updated prepacked weight buffer
            W = template_buffer_node.inputs[1]
            Y = template_buffer_node

            assert flag_template_buffer_has_other_users is not None
            template_buffer_has_other_users = flag_template_buffer_has_other_users

        template_buffer = Y
        gemm_output_buffer = template_buffer

        epilogues: list[ir.IRNode] = []
        reindexers: list[Callable[[list[Any]], list[Any]] | None] = []
        epilogue_creators: list[Callable[[ir.Buffer], ir.Pointwise]] = []
        fake_buffers: list[ir.Buffer] = []
        Y_aliases: OrderedSet[str] = OrderedSet()

        use_local_acc = (
            self.layout.dtype != torch.float
            or template_buffer_has_other_users
            or int8_gemm
            or self.padded_n != self.n
            or self.maybe_k_slicing()
            or (epilogue_nodes and epilogue_nodes[-1].get_dtype() != self.layout.dtype)
        )

        # TODO(jgong5): for int8 gemm, bias-add is handled outside of gemm template,
        # but we'd better move it here to align with fp.
        if inp is not None and self.beta != 0 and not int8_gemm:
            # add an epilogue for bias add
            def _bias_add_epilogue(buf):
                return create_epilogue_with_attr(
                    buf, "bias_add", other=inp, beta=self.beta, dtype=self.layout.dtype
                )

            epilogue_creators.append(_bias_add_epilogue)

        if self.epilogue_creator is not None:
            epilogue_creators.append(self.epilogue_creator)

        # When the GEMM output buffer is localized but it has users other than the epilogue nodes,
        # we need to copy the value in the GEMM output local buffer to a global buffer.
        def need_copy_from_local_to_global_buffer_epilogue(
            use_local_acc, template_buffer_has_other_users, epilogue_creators
        ):
            # The GEMM output buffer is a global buffer, thus copy is not needed.
            if not use_local_acc:
                return False

            # The possible value of template_buffer_has_other_users is (None, False, True)
            # It is None when generating the gemm template during autotune and it will have value during scheduler codegen.
            # extra copy_from_local_to_global_buffer_epilogue is not needed in either of the below two cases:
            #   1. template_buffer_has_other_users is None (i.e. when doing the codegen during autotune)
            #   2. template_buffer_has_other_users is False, which means it's safe to keep the value in the
            #       GEMM output buffer in local buffer only (no users outside of the epilogues will use its value).
            if not template_buffer_has_other_users:
                return False

            # When bias is not None or self.epilogue_creator is not None,
            # there will be epilogue_creators after the GEMM.
            # The GEMM output buffer is localized while
            # the output buffer of the epilogue_creators is a global buffer.
            if epilogue_creators:
                return False

            return True

        if need_copy_from_local_to_global_buffer_epilogue(
            use_local_acc, template_buffer_has_other_users, epilogue_creators
        ):

            def copy_from_local_to_global_buffer_epilogue(input_buffer: ir.Buffer):
                dtype = self.layout.dtype
                input_loader = input_buffer.make_loader()

                def copy_inner(index):
                    input = input_loader(index)
                    result = ops.to_dtype(input, dtype)
                    return result

                return ir.Pointwise(
                    device=input_buffer.get_device_or_error(),
                    dtype=self.layout.dtype,
                    inner_fn=copy_inner,
                    ranges=input_buffer.get_size(),
                )

            epilogue_creators.append(copy_from_local_to_global_buffer_epilogue)

        # NOTE [How CPP GEMM template epilogues are organized]
        #   gemm_output_buffer
        #     --> zero or more in-template epilogues (created by `epilogue_creators`) -->
        #   template_buffer
        #     --> zero or more out-of-template epilogues (`epilogue_nodes`) -->
        #   Y
        if epilogue_creators:
            assert isinstance(template_buffer, ir.IRNode)
            gemm_output_name = f"{template_buffer.get_name()}_GemmOut"
            gemm_output_buffer = ir.Buffer(
                name=gemm_output_name,
                # pyrefly: ignore [missing-attribute]
                layout=template_buffer.layout,
            )
            current_input_buffer = gemm_output_buffer
            for i, creator in enumerate(epilogue_creators):
                if i == len(epilogue_creators) - 1:
                    buffer_name = template_buffer.get_name()
                else:
                    buffer_name = f"{gemm_output_name}_epilogue_{i}"
                epilogues.append(
                    ir.ComputedBuffer(
                        name=buffer_name,
                        # pyrefly: ignore [missing-attribute]
                        layout=template_buffer.layout,
                        data=creator(current_input_buffer),
                    )
                )
                fake_buffers.append(current_input_buffer)
                Y_aliases.add(current_input_buffer.get_name())
                reindexers.append(None)
                if i < len(epilogue_creators) - 1:
                    current_input_buffer = ir.Buffer(
                        name=buffer_name,
                        # pyrefly: ignore [missing-attribute]
                        layout=template_buffer.layout,
                    )

        assert isinstance(Y, (ir.Buffer, ir.ReinterpretView))
        Y_2d: ir.Buffer | ir.ReinterpretView = Y

        if epilogue_nodes:
            if not template_buffer_has_other_users:
                assert isinstance(template_buffer, ir.IRNode)
                Y_aliases.add(template_buffer.get_name())
            epilogues.extend(epilogue_nodes)
            assert Y.get_numel() == epilogues[-1].get_numel()
            Y = cast(ir.Buffer, epilogues[-1])
            assert isinstance(template_buffer, ir.Buffer)
            Y_2d, reindexers = gen_2d_view_of_epilogue_buf(
                Y,
                template_buffer,
                epilogue_nodes,
                reindexers,
                default_reindexers=self.get_default_reindexers(epilogue_nodes),
            )

        output_dtype, compute_dtype = get_gemm_template_output_and_compute_dtype(
            X.get_dtype()
        )
        micro_gemm = create_micro_gemm(
            f"{kernel.kernel_name}_micro_gemm",
            self.m,
            self.n,
            self.k,
            input_dtype=X.get_dtype(),
            input2_dtype=W.get_dtype(),
            output_dtype=output_dtype,
            compute_dtype=compute_dtype,
            alpha=self.alpha,
            num_threads=self.num_threads,
            use_ref=not self.is_woq_int4(),
            q_group_size=self.q_group_size(),
        )
        assert micro_gemm is not None
        micro_gemm.use_local_vnni_blocking(not self.should_block_weights)
        assert self.register_blocking == micro_gemm.register_blocking
        self.log_blockings()
        if isinstance(micro_gemm, CppMicroGemmAMX):
            counters["inductor"]["cpp_micro_gemm_amx_counter"] += 1
        if isinstance(micro_gemm, CppMicroBrgemm):
            counters["inductor"]["cpp_micro_brgemm_counter"] += 1

        L1_cache_size = torch.cpu.get_capabilities().get(
            "l1d_cache_size", 0
        )  # per core cache size in Bytes
        assert L1_cache_size > 0, f"Expect L1_cache_size > 0 but got {L1_cache_size}"

        L2_cache_size = torch.cpu.get_capabilities().get(
            "l2_cache_size", 0
        )  # per core cache size in Bytes
        assert L2_cache_size > 0, f"Expect L2_cache_size > 0 but got {L2_cache_size}"

        options = dict(
            X=X,
            W=W,
            inp=inp,
            Y=Y,
            N=self.n,
            K=self.k,
            PADDED_N=self.padded_n,
            GemmOut=gemm_output_buffer,
            aliases={alias: Y.get_name() for alias in Y_aliases},
            beta=self.beta,
            alpha=self.alpha,
            num_threads=self.num_threads,
            micro_gemm=micro_gemm,
            is_dynamic_M=self.is_dynamic_M,
            template=self,
            kernel=kernel,
            export_declaration=get_export_declaration(),
            epilogue_nodes=epilogues,
            reindexers=reindexers,
            Y_2d=Y_2d,
            use_local_acc=use_local_acc,
            maybe_k_slicing=self.maybe_k_slicing(),
            x_scale=x_scale,
            x_zp=x_zp,
            w_scale=w_scale,
            w_zp=w_zp,
            acc_buf_dtype=torch.int32 if int8_gemm else torch.float,
            DTYPE_TO_CPP=DTYPE_TO_CPP,
            L1_cache_size=L1_cache_size,
            L2_cache_size=L2_cache_size,
            config=config,
            fake_buffers=fake_buffers,
            is_woq_int4=self.is_woq_int4(),
            q_group_size=q_group_size_node,
            qscale_and_zeros=qscale_and_zeros,
            cpu_count=os.cpu_count(),
        )
        return options