def linear_binary(
            x: TensorBox, y: TensorBox, w: TensorBox, b: TensorBox, attr, layout=None
        ):
            x_size = x.get_size()
            if len(x_size) > 2:
                # GEMM template needs 2D input, normalize input shape here
                x = view(x, [-1, x_size[-1]])
            y_size = y.get_size()
            if len(y_size) > 2:
                y = view(y, [-1, y_size[-1]])
            if b is not None:
                b = ir.ExternKernel.realize_input(b)  # type: ignore[assignment]
            choices: list[ChoiceCaller] = []
            if config.max_autotune or config.max_autotune_gemm:
                transposed_w = permute(w, [1, 0])
                *_, layout, x, transposed_w, y = mm_args(
                    x, transposed_w, y, layout=layout
                )
                if use_cpp_gemm_template(layout, x, transposed_w):

                    def epilogue_creator(buf):
                        return create_epilogue_with_attr(buf, attr, other=y)

                    kwargs = {
                        "has_bias": b is not None,
                        "trans_w": True,
                        "epilogue_creator": epilogue_creator,
                    }

                    # pyrefly: ignore [bad-typed-dict-key, unsupported-operation]
                    kwargs["input_indices"] = [0, 2, 1] if b is None else [3, 0, 2, 1]
                    CppGemmTemplate.add_choices(
                        choices,
                        layout,
                        [x, y, w] if b is None else [x, y, w, b],
                        **kwargs,  # type: ignore[arg-type]
                    )
            if len(choices) == 0 or use_aten_gemm_kernels():
                kwargs = dict(attr=attr)
                if b is None:
                    kwargs["B"] = None
                choices.append(
                    aten_mkldnn_linear_binary.bind(
                        [x, y, w] if b is None else [x, y, w, b],
                        layout,
                        **kwargs,
                    )
                )
            assert w.get_name() in V.graph.constants
            input_gen_fns = {
                2: lambda x: V.graph.constants[x.get_name()],
            }
            result, _ = autotune_select_algorithm(
                "linear_binary",
                choices,
                [x, y, w] if b is None else [x, y, w, b],
                layout,
                input_gen_fns=input_gen_fns,
            )
            if len(x_size) > 2:
                result = view(result, (*x_size[:-1], result.get_size()[-1]))
            return result