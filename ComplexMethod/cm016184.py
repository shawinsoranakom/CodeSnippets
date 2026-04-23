def wrapper(config, *args, **kwargs):
            try:
                return func(config, *args, **kwargs)
            except torch.OutOfMemoryError:
                print(
                    f"[SKIP] OOM for {backend_name or func.__name__} with shape {config.shape}"
                )
                cleanup_memory()
            except RuntimeError as e:
                error_msg = str(e)
                if "out of resource" in error_msg or "OutOfMemoryError" in error_msg:
                    print(
                        f"[SKIP] Triton OOM for {backend_name or func.__name__} with shape {config.shape}"
                    )
                    cleanup_memory()
                elif "No valid triton configs" in error_msg:
                    print(
                        f"[SKIP] No valid Triton config for {backend_name or func.__name__} with shape {config.shape}"
                    )
                else:
                    print(
                        f"[SKIP] Runtime error for {backend_name or func.__name__} with shape {config.shape}: {str(e)[:100]}"
                    )
            except Exception as e:
                print(
                    f"[SKIP] Error for {backend_name or func.__name__} with shape {config.shape}: {str(e)[:100]}"
                )

            # Return appropriate NaN result based on function type
            if return_dict:
                # For run_single_experiment: return dict with NaN for all backends
                nan_result = ExperimentResults(
                    fwd_time=float("nan"),
                    bwd_time=float("nan") if config.calculate_bwd_time else None,
                )
                results = dict.fromkeys(config.backends, nan_result)
                results["flex"] = ExperimentResults(
                    fwd_time=float("nan"),
                    bwd_time=float("nan") if config.calculate_bwd_time else None,
                    sparsity=None,
                )
                return results
            else:
                # For individual backend functions: return single ExperimentResults
                return ExperimentResults(
                    fwd_time=float("nan"),
                    bwd_time=float("nan") if config.calculate_bwd_time else None,
                )