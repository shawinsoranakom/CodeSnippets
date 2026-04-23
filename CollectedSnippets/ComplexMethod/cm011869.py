def qlinear_binary(
            x: TensorBox,
            x_scale,
            x_zp,
            packed_weight: TensorBox,
            w_scale: TensorBox,
            w_zp: TensorBox,
            x2: TensorBox,
            bias: TensorBox,
            o_scale,
            o_zero_point,
            output_dtype,
            x2_scale,
            x2_zp,
            binary_attr,
            alpha,
            unary_attr,
            unary_scalars,
            unary_algorithm,
            layout=None,
        ):
            x_size = x.get_size()
            x2_size = x2.get_size()
            assert len(x_size) == len(x2_size)
            if len(x_size) > 2 and binary_attr in ["add", "sum"]:
                # GEMM template needs 2D input, normalize input shape here
                x = view(x, [-1, x_size[-1]])
                x2 = view(x2, [-1, x2_size[-1]])
            if not isinstance(x_scale, ir.TensorBox):
                assert type(x_scale) is float
                x_scale = V.graph.add_tensor_constant(
                    torch.tensor(x_scale, dtype=torch.float32), name="x_scale"
                )
            else:
                x_scale.realize()
                if all(dim == 1 for dim in x_scale.get_size()):
                    # Corner-case discovered with LLaMA series.
                    # If all outer dims of x_scale are 1, make it a 0D tensor.
                    # Otherwise, epilogue creator will run into indexing issues.
                    x_scale = view(x_scale, [])
                assert len(x_scale.get_size()) in [0, 1], "x_scale must be 0D or 1D"

            if x_zp is None:
                x_zp = V.graph.add_tensor_constant(
                    torch.tensor(0, dtype=torch.int32), name="x_zp"
                )

            if w_zp is None:
                w_zp = V.graph.add_tensor_constant(
                    torch.tensor(0, dtype=torch.int32), name="w_zp"
                )

            if not isinstance(x_zp, ir.TensorBox):
                assert type(x_zp) is int
                x_zp = V.graph.add_tensor_constant(
                    torch.tensor(x_zp, dtype=torch.int32), name="x_zp"
                )
            else:
                x_zp.realize()

            # When channels less than 8, w_scale/w_zp is Pointwise instead of ConstantBuffer
            # Refer to
            # https://github.com/pytorch/pytorch/blob/f353d17755ed23b02924c962a86ff99a3405fe10/torch/_inductor/graph.py#L570-L577
            w_scale.realize()
            w_zp.realize()
            if w_zp.get_dtype() != torch.int32 and isinstance(
                ir.InputsKernel.unwrap_storage_for_input(w_zp),
                ir.ConstantBuffer,
            ):
                w_zp_tensor = V.graph.constants[w_zp.get_name()].to(torch.int32)
                w_zp = V.graph.add_tensor_constant(  # type: ignore[assignment]
                    torch.tensor(w_zp_tensor, dtype=torch.int32), name=w_zp.get_name()
                )
            if binary_attr == "sum":
                if output_dtype in [
                    torch.float32,
                    torch.bfloat16,
                ] and x2.get_dtype() in [torch.float32, torch.bfloat16]:
                    if x2.get_dtype() != output_dtype:
                        # For int8-mixed-bf16 quantization and inplace add,
                        # there is case when accum dtype is float32 but output dtype is bfloat16.
                        # Since the accum will be inplaced changed with post op sum,
                        # we will do accum dtype conversion here.
                        x2 = to_dtype(x2, output_dtype)
                else:
                    assert x2.get_dtype() == output_dtype, (
                        "dtype of accum for qlinear post op sum should be the same as output"
                    )
            x2_dtype = x2.get_dtype()
            bias_dtype = bias.get_dtype() if bias is not None else None
            choices: list[ChoiceCaller] = []
            if (config.max_autotune or config.max_autotune_gemm) and binary_attr in [
                "add",
                "sum",
            ]:
                *_, layout, x, packed_weight, x2 = mm_args(
                    x, packed_weight, x2, layout=layout, out_dtype=output_dtype
                )
                if (
                    isinstance(
                        ir.InputsKernel.unwrap_storage_for_input(x_zp),
                        ir.ConstantBuffer,
                    )
                    and len(x_zp.get_layout().size) == 0  # Per tensor quant of act
                    and isinstance(
                        ir.InputsKernel.unwrap_storage_for_input(w_zp),
                        ir.ConstantBuffer,
                    )
                    and torch.equal(
                        torch.zeros_like(V.graph.constants[w_zp.get_name()]),
                        V.graph.constants[w_zp.get_name()],
                    )  # We only compensate MatrixB and assume B_zp is 0 to avoid the compensation of MatrixA
                    and use_cpp_gemm_template(layout, x, packed_weight)
                ):
                    W_tensor = V.graph.constants[packed_weight.get_name()]
                    W_tensor = W_tensor.to_dense()
                    (
                        use_int8_fast_compensation_path,
                        weight_compens,
                        x_w_scale,
                    ) = create_int8_compensation(
                        W_tensor,
                        packed_weight,
                        x_scale,
                        x_zp,
                        w_scale,
                    )

                    def epilogue_creator(input_buffer):
                        # Epilogue to convert from s32 to f32 for u8s8f32
                        assert output_dtype in [
                            torch.float32,
                            torch.bfloat16,
                            torch.uint8,
                            torch.int8,
                        ]

                        input_loader = input_buffer.make_loader()
                        x2_loader = x2.make_loader()
                        weight_compens_loader = weight_compens.make_loader()
                        x_w_scale_loader = None
                        if use_int8_fast_compensation_path:
                            assert x_w_scale is not None
                            x_w_scale_loader = x_w_scale.make_loader()
                        x_scale_loader = x_scale.make_loader()
                        w_scale_loader = w_scale.make_loader()
                        x_zp_loader = x_zp.make_loader()
                        nonlocal bias
                        bias_loader = None
                        if bias is not None:
                            bias_loader = bias.make_loader()

                        def inner_fn(index):
                            nonlocal bias
                            input = input_loader(index)
                            _x2 = x2_loader(index)
                            _x_scale = None
                            _x_zp = None
                            _w_scale = None
                            weight_compens_index = (index[-1],)
                            if not use_int8_fast_compensation_path:
                                _x_scale = x_scale_loader(())
                                _x_zp = x_zp_loader(())
                                _w_scale = w_scale_loader(weight_compens_index)
                            # MicroKernel Output is with int32: cvt to FP32 before doing compensation
                            input = ops.to_dtype(input, torch.float32)
                            _weight_compo = weight_compens_loader(weight_compens_index)
                            _x_w_scale = None
                            if use_int8_fast_compensation_path:
                                assert x_w_scale_loader is not None
                                _x_w_scale = x_w_scale_loader(weight_compens_index)
                            # Step 1: Doing compensation to cvt fp32
                            temp = codegen_int8_gemm_template_compensation(
                                use_int8_fast_compensation_path,
                                input,
                                _weight_compo,
                                _x_scale,
                                _x_zp,
                                _w_scale,
                                _x_w_scale,
                            )
                            # Step 2: add Bias if applicable
                            if bias is not None:
                                # pyrefly: ignore [not-callable]
                                _bias = bias_loader(weight_compens_index)
                                nonlocal bias_dtype
                                assert bias_dtype in [torch.float32, torch.bfloat16]
                                if bias_dtype == torch.bfloat16:
                                    _bias = ops.to_dtype(_bias, torch.float32)
                                temp = ops.add(temp, _bias)

                            # Step 3: Binary add
                            nonlocal x2_dtype
                            assert x2_dtype in [torch.float32, torch.bfloat16]
                            if x2_dtype == torch.bfloat16:
                                _x2 = ops.to_dtype(_x2, torch.float32)
                            temp = ops.add(temp, _x2)

                            return temp

                        output_buf = ir.Pointwise(
                            device=input_buffer.get_device(),
                            dtype=torch.float32,  # Hardcode to FP32 for u8s8f32
                            inner_fn=inner_fn,
                            ranges=input_buffer.get_size(),
                        )

                        # Step 4: Unary post op if has
                        if unary_attr != "none":
                            output_buf = create_epilogue_with_attr(
                                output_buf,
                                unary_attr,
                                scalars=unary_scalars,
                                algorithm=unary_algorithm,
                            )

                        # Step 5: Cast output to Target Dtype
                        if output_dtype == torch.bfloat16:
                            output_cast_loader = output_buf.make_loader()

                            def inner_fn_cast_output_to_bf16(index):
                                input = output_cast_loader(index)
                                return ops.to_dtype(input, output_dtype)

                            output_buf = ir.Pointwise(
                                device=output_buf.get_device_or_error(),
                                dtype=output_dtype,
                                inner_fn=inner_fn_cast_output_to_bf16,
                                ranges=output_buf.get_size(),
                            )
                        elif output_dtype in [torch.uint8, torch.int8]:
                            from .lowering import _create_constants

                            requant_input_loader = output_buf.make_loader()

                            def inner_fn_requant(index, scale, zero_point):
                                input = requant_input_loader(index)
                                inv_scale, zero_point = _create_constants(
                                    1.0 / scale, zero_point, dtype=torch.float32
                                )
                                val = ops.round(input * inv_scale) + zero_point
                                if output_dtype == torch.uint8:
                                    qmin, qmax = _create_constants(
                                        0, 255, dtype=torch.float32
                                    )
                                else:
                                    qmin, qmax = _create_constants(
                                        -128, 127, dtype=torch.float32
                                    )
                                clamped = ops.minimum(ops.maximum(val, qmin), qmax)
                                return ops.to_dtype(clamped, torch.uint8)

                            output_buf = ir.Pointwise(
                                device=output_buf.get_device_or_error(),
                                dtype=torch.uint8,
                                inner_fn=functools.partial(
                                    inner_fn_requant,
                                    scale=float(o_scale),
                                    zero_point=int(o_zero_point),
                                ),
                                ranges=output_buf.get_size(),
                            )

                        return output_buf

                    CppGemmTemplate.add_choices(
                        choices,
                        layout,
                        [x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2]
                        if bias is None
                        else [x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2, bias],
                        has_bias=bias is not None,
                        epilogue_creator=epilogue_creator,
                        # Reorder bias and x2
                        input_indices=[0, 3, 1, 2, 4, 5, 6]
                        if bias is None
                        else [7, 0, 3, 1, 2, 4, 5, 6],
                    )

            if len(choices) == 0 or use_aten_gemm_kernels():
                kwargs = dict(
                    output_scale=o_scale,
                    output_zero_point=o_zero_point,
                    output_dtype=output_dtype,
                    other_scale=x2_scale,
                    other_zp=x2_zp,
                    binary_post_op=binary_attr,
                    binary_alpha=alpha,
                    unary_post_op=unary_attr,
                    unary_post_op_args=unary_scalars,
                    unary_post_op_algorithm=unary_algorithm,
                )
                if bias is None:
                    kwargs["bias"] = None
                choices.append(
                    aten_mkldnn_qlinear_binary.bind(
                        (x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2)
                        if bias is None
                        else (x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2, bias),
                        layout,
                        **kwargs,
                    )
                )
            assert packed_weight.get_name() in V.graph.constants
            input_gen_fns = {
                3: lambda x: V.graph.constants[x.get_name()],
                4: lambda x: V.graph.constants[x.get_name()],
                5: lambda x: V.graph.constants[x.get_name()],
            }
            if bias is not None:
                input_gen_fns[7] = lambda x: V.graph.constants[x.get_name()]  # For bias
            result, _ = autotune_select_algorithm(
                "qlinear_binary",
                choices,
                [x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2]
                if bias is None
                else [x, x_scale, x_zp, packed_weight, w_scale, w_zp, x2, bias],
                layout,
                input_gen_fns=input_gen_fns,
            )
            if (
                isinstance(result.data.data, ir.CppTemplateBuffer)
                and binary_attr == "sum"
                and result.data.data.layout == x2.get_layout()
            ):
                # In this case, since x2 is inplace updated when binary_attr is "sum"
                # we update the layout of result to view of x2
                result = ir.TensorBox.create(
                    ir.CppTemplateBuffer(
                        layout=ir.NonOwningLayout(
                            ir.ReinterpretView(data=x2, layout=x2.get_layout())
                        ),
                        inputs=result.data.data.inputs,  # type: ignore[arg-type]
                        make_kernel_render=result.data.data.make_kernel_render,  # type: ignore[arg-type]
                        template=result.data.data.template,
                        choice=result.data.data.choice,
                    )
                )
            if len(x_size) > 2 and binary_attr in ["add", "sum"]:
                result = view(result, (*x_size[:-1], result.get_size()[-1]))  # type: ignore[arg-type]
            return result