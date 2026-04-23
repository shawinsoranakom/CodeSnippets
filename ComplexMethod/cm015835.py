def run_test(use_fast_accum):
            with fresh_cache():
                with config.patch(
                    {
                        "max_autotune": True,
                        "max_autotune_gemm_backends": "CUTLASS",
                        "cutlass.cutlass_max_profiling_configs": 2,
                    }
                ):
                    with mock.patch(
                        "torch._inductor.kernel.mm.autotune_select_algorithm",
                        wraps=select_no_algorithm,
                    ) as sa:
                        with self.assertRaisesRegex(
                            InductorError, r".*NoValidChoicesError.*"
                        ):
                            linear_compiled(
                                x_fp8,
                                x_inverse_scale,
                                w_t_fp8,
                                w_inverse_scale,
                                bias,
                                use_fast_accum,
                            )

                        args, _ = sa.call_args
                        _, choices, _, _ = args
                        cuda_template_count = 0
                        for choice in choices:
                            if isinstance(choice, CUTLASSTemplateCaller):
                                choice_info = choice.info_dict()
                                op_conf_name = choice_info.get("op_conf_name", "")
                                if not isinstance(op_conf_name, str):
                                    raise AssertionError(
                                        f"Expected op_conf_name to be str, got {type(op_conf_name)}"
                                    )
                                if use_fast_accum:
                                    if "fastaccum" not in op_conf_name:
                                        raise AssertionError(
                                            "Only fastaccum Kernels should have been allowed"
                                        )
                                else:
                                    if "fastaccum" in op_conf_name:
                                        raise AssertionError(
                                            "fastaccum Kernels should have been filtered"
                                        )
                                cuda_template_count += 1
                        if cuda_template_count <= 0:
                            raise AssertionError("No CUTLASSTemplateCaller choices")