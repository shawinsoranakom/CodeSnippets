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