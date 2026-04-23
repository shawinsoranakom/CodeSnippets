def benchmark_when_ready() -> bool:
                from torch._inductor.runtime.triton_heuristics import (
                    NoTritonConfigsError,
                )

                try:
                    # Wait for all compilations to complete
                    for fut in (
                        future_and_mod_l1[0],
                        future_and_mod_l2[0],
                        future_and_mod_l1_fused[0],
                    ):
                        if fut is not None:
                            fut.result()

                    ms1, path1 = self.benchmark_codegened_module(
                        future_and_mod_l1[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms1):
                        why("register spilling of the first kernel")
                        return False

                    ms2, path2 = self.benchmark_codegened_module(
                        future_and_mod_l2[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms2):
                        why("register spilling of the second kernel")
                        return False

                    ms_fused, path_fused = self.benchmark_codegened_module(
                        future_and_mod_l1_fused[1],
                        # pyrefly: ignore [bad-argument-type]
                        device,
                    )
                    if math.isinf(ms_fused):
                        why("register spilling of the fused kernel")
                        return False

                    log_fusion(ms_fused, ms1, ms2)

                    if (
                        is_metric_table_enabled("slow_fusion")
                        and ms_fused >= ms1 + ms2
                        and (path1, path2) not in self.logged_slow_fusion
                    ):
                        self.logged_slow_fusion.add((path1, path2))
                        get_metric_table("slow_fusion").add_row(
                            lambda: {
                                "kernel1_path": path1,
                                "kernel1_latency": ms1,
                                "kernel2_path": path2,
                                "kernel2_latency": ms2,
                                "fused_kernel_path": path_fused,
                                "fused_kernel_latency": ms_fused,
                                "slow_down_ratio": ms_fused / (ms1 + ms2),
                            }
                        )

                    return ms_fused < ms1 + ms2

                except NoTritonConfigsError:
                    return False

                except CompilationError as e:
                    if "Loop-carried variable" in str(e):
                        return True
                    raise