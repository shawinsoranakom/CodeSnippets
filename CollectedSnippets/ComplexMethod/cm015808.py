def test_workspace_allocation_error(self):
            torch._C._cuda_clearCublasWorkspaces()

            prev = torch._inductor.cudagraph_trees.clear_cublas_manager

            try:
                torch._inductor.cudagraph_trees.clear_cublas_manager = (
                    contextlib.nullcontext
                )

                @torch.compile()
                def foo(x, y):
                    return x @ x

                inps = [torch.rand([400, 400], device="cuda") for _ in range(2)]

                thrown = False
                try:
                    foo(*inps)
                except Exception as e:
                    thrown = True
                    if not IS_ARM64:
                        # CUDA uses gemm/gemm_internal_cublas, ROCm uses bgemm_internal_cublaslt
                        self.assertTrue(
                            "at::cuda::blas::gemm<float, float>" in str(e)
                            or "at::cuda::blas::gemm_internal_cublas<float, float>"
                            in str(e)
                            or "at::cuda::blas::bgemm_internal_cublaslt<float, float>"
                            in str(e)
                        )
                        # CUDA uses getCurrentCUDABlasHandle/getNewWorkspace,
                        # ROCm uses getNewCUDABlasLtWorkspace/getCUDABlasLtWorkspace
                        self.assertTrue(
                            "getCurrentCUDABlasHandle" in str(e)
                            or "getNewWorkspace" in str(e)
                            or "CUDABlasLtWorkspace" in str(e)
                        )

                self.assertTrue(thrown)

            finally:
                torch._C._cuda_clearCublasWorkspaces()
                torch._inductor.cudagraph_trees.clear_cublas_manager = prev
                torch._inductor.cudagraph_trees.get_container(
                    self.device_idx
                ).tree_manager = None