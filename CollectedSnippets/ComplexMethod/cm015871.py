def _test_triton_kernel_to_post_grad_tracing(self, device):
        a = torch.randn(10, 20, device=device)
        b = torch.randn(20, 30, device=device)
        c = torch.randn(10, 30, device=device)
        example_inputs = (a, b, c)

        model = Model().to(device)
        filepath = None

        for backend in ["aot_inductor", "inductor"]:
            reset_inductor_kernel_provenance_debug_handle()
            try:
                with config.patch(
                    {
                        "trace.debug_dir": tempfile.mkdtemp(),
                        "force_disable_caches": True,
                    }
                ):
                    with self.assertLogs(
                        logging.getLogger("torch._inductor.debug"),
                        level=logging.WARNING,
                    ) as cm:
                        if backend == "aot_inductor":
                            AOTIRunnerUtil.run(model, example_inputs)
                        else:
                            ep = torch.export._trace._export(model, example_inputs)
                            compiled = torch.compile(ep.module(), backend=backend)
                            compiled(*example_inputs)
                    self.assertEqual(len(cm.output), 1)
                    m = re.match(r"WARNING.* debug trace: (.*)", cm.output[0])
                    self.assertTrue(m)
                    filepath = Path(m.group(1))
                    if device == "cuda" or device == "xpu":
                        expected_mapping = [
                            (
                                "cppCodeToPost",
                                {
                                    "triton_poi_fused_mul_0:1": ["mul"],
                                    "triton_poi_fused_addmm_gelu_1:3": [
                                        "mul_3",
                                        "mul_1",
                                        "add_tensor",
                                        "add",
                                        "erf",
                                        "mul_2",
                                    ],
                                },
                            ),
                            (
                                "postToCppCode",
                                {
                                    "mul": ["triton_poi_fused_mul_0:1"],
                                    "mul_3": ["triton_poi_fused_addmm_gelu_1:3"],
                                    "mul_1": ["triton_poi_fused_addmm_gelu_1:3"],
                                    "add_tensor": ["triton_poi_fused_addmm_gelu_1:3"],
                                    "add": ["triton_poi_fused_addmm_gelu_1:3"],
                                    "erf": ["triton_poi_fused_addmm_gelu_1:3"],
                                    "mul_2": ["triton_poi_fused_addmm_gelu_1:3"],
                                },
                            ),
                            (
                                "postToPre",
                                {
                                    "mul": ["mul"],
                                    "mm_default": ["addmm"],
                                    "add_tensor": ["addmm"],
                                    "mul_1": ["gelu"],
                                    "mul_2": ["gelu"],
                                    "erf": ["gelu"],
                                    "add": ["gelu"],
                                    "mul_3": ["gelu"],
                                },
                            ),
                            (
                                "preToPost",
                                {
                                    "mul": ["mul"],
                                    "addmm": ["mm_default", "add_tensor"],
                                    "gelu": ["mul_1", "mul_2", "erf", "add", "mul_3"],
                                },
                            ),
                        ]
                        if backend == "aot_inductor" and device == "cuda":
                            expected_mapping[0][1]["aoti_torch_cuda_mm_out:2"] = [
                                "mm_default"
                            ]
                            expected_mapping[1][1]["mm_default"] = [
                                "aoti_torch_cuda_mm_out:2"
                            ]
                        elif backend == "aot_inductor" and device == "xpu":
                            expected_mapping[0][1]["aoti_torch_xpu_mm_out:2"] = [
                                "mm_default"
                            ]
                            expected_mapping[1][1]["mm_default"] = [
                                "aoti_torch_xpu_mm_out:2"
                            ]
                        else:
                            expected_mapping[0][1]["extern_kernels.mm:2"] = [
                                "mm_default"
                            ]
                            expected_mapping[1][1]["mm_default"] = [
                                "extern_kernels.mm:2"
                            ]
                        self._check_provenance_tracking_node_mappings(
                            filepath, expected_mapping
                        )
                    else:
                        if device != "cpu":
                            raise AssertionError
                        # check the inductor kernel to post grad nodes mapping is expected for cpu
                        if backend == "aot_inductor":
                            expected_data = {
                                "cpp_fused_mul_0:1": ["mul"],
                                "aoti_torch_cpu_addmm_out:2": ["addmm"],
                                "cpp_fused_gelu_1:3": [
                                    "mul_3",
                                    "mul_1",
                                    "add",
                                    "erf",
                                    "mul_2",
                                ],
                            }
                        else:
                            # backend == "inductor"
                            expected_data = {
                                "cpp_fused_mul_0:1": ["mul"],
                                "cpp_fused_gelu_1:3": [
                                    "mul_3",
                                    "mul_1",
                                    "add",
                                    "erf",
                                    "mul_2",
                                ],
                                "extern_kernels.addmm:2": ["addmm"],
                            }
                        self._check_provenance_tracing_kernel_to_post_grad(
                            filepath, expected_data
                        )

            finally:
                if filepath:
                    shutil.rmtree(filepath)