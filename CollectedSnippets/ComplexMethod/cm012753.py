def render(  # type: ignore[override]
        self,
        kernel: ROCmTemplateKernel,
        op: "CKGemmOperation",
        **kwargs,
    ) -> str:
        """
        The primary entry point for the code rendering process used in this template.
        """
        epilogue_nodes = kwargs.get("epilogue_nodes")
        assert epilogue_nodes is None or 0 == len(epilogue_nodes)
        template_buffer_node = kwargs.get("template_buffer_node")
        if template_buffer_node is not None:
            self.output_node = template_buffer_node
        # input nodes:
        # * X, W for matmul
        # * X, W, Bias for addmm
        # * X, W, inv_scale_x, inv_scale_w for scaled_mm
        # * X, W, inv_scale_x, inv_scale_w, Bias for scaled_mm with bias
        X, W = self.input_nodes[0], self.input_nodes[1]
        Y = self.output_node
        Bias = (
            self.input_nodes[2]
            if 3 == len(self.input_nodes)
            else self.input_nodes[4]
            if 5 == len(self.input_nodes)
            else None
        )
        has_bias = Bias is not None
        has_scale = len(self.input_nodes) in (4, 5)
        op = copy.deepcopy(op)

        # This parameter is converted into tuple because of change
        # from DeviceGemm_Xdl_CShuffleV3 to DeviceGemmMultiD_Xdl_CShuffle_V3.
        # The first tuple element corresponds to matmul result...
        if not isinstance(
            op.c_shuffle_block_transfer_scalar_per_vector_n_per_block, tuple
        ):
            op.c_shuffle_block_transfer_scalar_per_vector_n_per_block = (
                op.c_shuffle_block_transfer_scalar_per_vector_n_per_block,
            )

        if has_scale:
            scale_x = self.input_nodes[2]
            scale_w = self.input_nodes[3]
            if 1 == scale_x.get_numel() and 1 == scale_w.get_numel():
                # tensorwise scale for both X, W
                if has_bias:
                    op.c_elementwise_op = "ScaleAdd"
                else:
                    op.c_elementwise_op = "Scale"
            else:
                # rowwise scale for both X, W
                if has_bias:
                    op.c_elementwise_op = "MultiplyMultiplyAdd"
                else:
                    op.c_elementwise_op = "MultiplyMultiply"
                op.c_shuffle_dtype = "F32"
                op.ds_layouts = (
                    torch_layout_to_ck_layout(scale_x.get_layout()),
                    torch_layout_to_ck_layout(scale_w.get_layout()),
                )
                op.ds_element_dtypes = (
                    self._TORCH_DTYPE_TO_CK[scale_x.get_layout().dtype],
                    self._TORCH_DTYPE_TO_CK[scale_w.get_layout().dtype],
                )
                op.c_shuffle_block_transfer_scalar_per_vector_n_per_block += (1, 1)
        else:
            scale_x = None
            scale_w = None

        bias_dtype = ""
        if Bias is not None:
            bias_layout = torch_layout_to_ck_layout(Bias.get_layout())
            bias_dtype = self._TORCH_DTYPE_TO_CK[Bias.get_layout().dtype]
            op.ds_layouts += (bias_layout,)
            op.ds_element_dtypes += (bias_dtype,)
            if not has_scale:
                op.c_elementwise_op = "Bilinear"
            # c_shuffle_dtype is also used for adding bias to matmul result
            # before converting down to the result dtype
            op.c_shuffle_dtype = op.acc_dtype
            # this parameter needs to be set accordingly to bias stride for correct accumulation
            if bias_layout == "Row":
                # bias has (N, ) shape
                bias_shuffle_block_transfer_scalar_per_vector_n_per_block = (
                    op.c_shuffle_block_transfer_scalar_per_vector_n_per_block
                )
            elif bias_layout == "Col":
                # bias has (M, 1) shape
                bias_shuffle_block_transfer_scalar_per_vector_n_per_block = (1,)
            else:
                raise AssertionError(
                    "Bias layout is neither row-major nor column-major"
                )
            # ...and the second tuple element corresponds to the bias
            op.c_shuffle_block_transfer_scalar_per_vector_n_per_block += (
                bias_shuffle_block_transfer_scalar_per_vector_n_per_block
            )

        instance_definition, instance_type = self.emit_ck_instance(op)

        version_comment = rf"""/**
* Generated code for CK inductor backend
* See {type(self).__module__}.{type(self).__qualname__}
*
* Template instance {op}
*
* {torch.__version__=}
* torch.version.git_version={getattr(torch.version, "git_version", "None")}
*/
"""
        epilogue = None

        if op.c_elementwise_op == "Bilinear" and scale_w is None:
            epilogue = f"Bilinear {{ {self.alpha}, {self.beta} }}"

        elif op.c_elementwise_op == "Scale":
            epilogue = "Scale { (inv_scale_w && inv_scale_x) ? (*inv_scale_w * *inv_scale_x) : 1.0f }"

        elif op.c_elementwise_op == "ScaleAdd":
            epilogue = "ScaleAdd { (inv_scale_w && inv_scale_x) ? (*inv_scale_w * *inv_scale_x) : 1.0f }"

        elif op.c_elementwise_op == "MultiplyMultiply":
            epilogue = "MultiplyMultiply {}"

        elif op.c_elementwise_op == "MultiplyMultiplyAdd":
            epilogue = "MultiplyMultiplyAdd {}"

        elif op.c_elementwise_op == "PassThrough":
            epilogue = "PassThrough {}"

        assert epilogue is not None, "CK GEMM epilogue is not set"

        size_arg_strs = ["M", "N", "K", "LDA", "LDB", "LDC", "LDD"]
        if self.is_batched:
            size_arg_strs.insert(0, "B")

        res = self._template_from_string(self.gemm_template).render(
            inline_utils=self.inline_utils(),
            headers=self.header().getvalue(),
            globals=self.globals().getvalue(),
            instance_definition=instance_definition,
            kernel_definition=kernel.def_kernel(
                inputs=[X, W, scale_x, scale_w, Bias],  # type: ignore[list-item]
                outputs=[Y],
                names_str="X, W, inv_scale_x, inv_scale_w, Bias, Y",
                input_reorder=self.input_reorder,
                size_args=[f"int32_t {arg}" for arg in size_arg_strs],
            ),
            instance_type=instance_type,
            a_element_dtype=op.a_element_dtype,
            b_element_dtype=op.b_element_dtype,
            c_element_dtype=op.c_element_dtype,
            bias_element_dtype=bias_dtype,
            alpha=self.alpha,
            beta=self.beta,
            a_elementwise_op="PassThrough {}",
            b_elementwise_op="PassThrough {}",
            epilogue=epilogue,
            has_bias=has_bias,
            ds_size=1
            if op.c_elementwise_op in ("Bilinear", "ScaleAdd")
            else 2
            if op.c_elementwise_op == "MultiplyMultiply"
            else 3
            if op.c_elementwise_op == "MultiplyMultiplyAdd"
            else 0,
            ds_names=", ".join(
                ["Bias"]
                if op.c_elementwise_op in ("Bilinear", "ScaleAdd")
                else ["inv_scale_x", "inv_scale_w"]
                if op.c_elementwise_op == "MultiplyMultiply"
                else ["inv_scale_x", "inv_scale_w", "Bias"]
                if op.c_elementwise_op == "MultiplyMultiplyAdd"
                else []
            ),
            ds_strides=", ".join(
                ["LDD"]
                if op.c_elementwise_op in ("Bilinear", "ScaleAdd")
                else ["0", "0"]
                if op.c_elementwise_op == "MultiplyMultiply"
                else ["0", "0", "LDD"]
                if op.c_elementwise_op == "MultiplyMultiplyAdd"
                else []
            ),
            version_comment=version_comment,
            is_batched=self.is_batched,
            ds_batch_strides=", ".join([]),  # FIXME when supporting baddbmm
        )

        if config.rocm.generate_test_runner:
            is_static_problem = all(is_static_int(arg) for arg in self.size_args())
            # NOTE: size_arg_strs is defined above
            size_arg_vals = (
                self.size_args()
                if is_static_problem
                else (
                    f"std::stoi(argv[{k}])" for k, _ in enumerate(self.size_args(), 1)
                )
            )
            size_args = dict(zip(size_arg_strs, size_arg_vals, strict=True))
            runtime_args = dict(
                zip(
                    [a.name for a in self.get_runtime_arg_info()],
                    self.get_runtime_arg_values(),
                )
            )
            runner_code = self._template_from_string(
                self.standalone_runner_template
            ).render(
                inline_utils=self.inline_utils().getvalue(),
                kernel_name=kernel.kernel_name,
                has_bias=has_bias,
                has_scale=has_scale,
                is_batched=self.is_batched,
                a_ck_dtype=op.a_element_dtype,
                b_ck_dtype=op.b_element_dtype,
                c_ck_dtype=op.c_element_dtype,
                bias_ck_dtype=op.ds_element_dtypes[0] if has_bias else "",
                scale_a_ck_dtype=op.ds_element_dtypes[0]
                if has_scale and 2 == len(op.ds_element_dtypes)
                else "BF16",
                scale_b_ck_dtype=op.ds_element_dtypes[1]
                if has_scale and 2 == len(op.ds_element_dtypes)
                else "BF16",
                a_torch_dtype=DTYPE_TO_CPP[X.get_layout().dtype],
                b_torch_dtype=DTYPE_TO_CPP[W.get_layout().dtype],
                c_torch_dtype=DTYPE_TO_CPP[Y.get_layout().dtype],
                bias_torch_dtype=DTYPE_TO_CPP[Bias.get_layout().dtype]
                if Bias is not None
                else "",
                scale_a_torch_dtype=DTYPE_TO_CPP[scale_x.get_layout().dtype]
                if scale_x is not None
                else "",
                scale_b_torch_dtype=DTYPE_TO_CPP[scale_w.get_layout().dtype]
                if scale_w is not None
                else "",
                a_layout=torch_layout_to_ck_layout(X.get_layout()),
                b_layout=torch_layout_to_ck_layout(W.get_layout()),
                c_layout=torch_layout_to_ck_layout(Y.get_layout()),
                bias_layout=torch_layout_to_ck_layout(Bias.get_layout())
                if Bias is not None
                else "",
                compile_cmd=rocm_compile_command(
                    ["<source_file_name>"], "<executable_name>", "exe"
                ),
                **size_args,
                **runtime_args,
            )
            res += runner_code

        return res