def benchmark_choices(
        cls,
        choices: Sequence[ChoiceCaller],
        autotune_args: AutotuneArgs,
        is_collective: bool = False,
    ) -> dict[ChoiceCaller, float]:
        """
        Benchmark a list of choices and return timing dict.
        """
        from torch._inductor.codegen.cutlass.kernel import CUTLASSTemplateCaller

        # Reorder only when CUTLASS is present: benchmark ATen/cuBLAS before
        # CUTLASS to collect valid fallback timings before any CUTLASS kernel
        # can corrupt the CUDA context (#171094)
        if any(isinstance(c, CUTLASSTemplateCaller) for c in choices):

            def choice_priority(c: ChoiceCaller) -> int:
                if isinstance(c, ExternKernelCaller):
                    return 0  # ATen/cuBLAS first
                elif isinstance(c, CUTLASSTemplateCaller):
                    return 2  # CUTLASS last
                else:
                    return 1  # Triton and others in the middle

            choices = sorted(choices, key=choice_priority)

        if is_collective:
            import torch.distributed as dist

            if not dist.is_initialized():
                log.warning(
                    "Collective op detected but distributed not initialized. "
                    "Falling back to regular benchmarking."
                )
                is_collective = False
            else:
                rank = dist.get_rank(None)  # Use default process group
                log.debug(
                    "Using collective benchmarking for %d choices on rank %d",
                    len(choices),
                    rank,
                )
        timings = {}
        for choice in choices:
            try:
                if is_collective:
                    timing = cls.benchmark_collective_choice(choice, autotune_args)
                else:
                    timing = cls.benchmark_choice(choice, autotune_args)
            except CUDACompileError:
                if not isinstance(choice, CUTLASSTemplateCaller):
                    log.exception(
                        "CUDA compilation error during autotuning: \n%s. \nIgnoring this choice."
                    )
                timing = float("inf")
            except NotImplementedError:
                log.warning("Not yet implemented", exc_info=True)
                timing = float("inf")
            except RuntimeError as e:
                msg = str(e)
                if "invalid argument" in msg:
                    msg += "\n\nThis may mean this GPU is too small for max_autotune mode.\n\n"
                elif "illegal memory access" in msg:
                    msg += "\n\nEither error in template or triton bug.\n"
                elif "unspecified launch failure" in msg:
                    msg += "\n\nAn unrecoverable unspecified launch failure was caught during autotuning."
                    msg += "\nPlease try re-running with TORCHINDUCTOR_AUTOTUNE_IN_SUBPROC=1.\n\n"

                if isinstance(choice, CUTLASSTemplateCaller):
                    log.debug(
                        "Runtime error during autotuning: \n%s. \nIgnoring this choice.",
                        msg,
                        exc_info=True,
                    )
                else:
                    log.error(
                        "Runtime error during autotuning: \n%s. \nIgnoring this choice.",
                        msg,
                    )
                timing = float("inf")
            except AssertionError as e:
                raise AssertionError(  # noqa: B904
                    f"Incorrect result from choice {choice}\n\n{e}"
                )
            except Exception as e:
                try:
                    from triton.runtime.autotuner import OutOfResources

                    if isinstance(e, OutOfResources):
                        log.warning(e)
                        timing = float("inf")
                    else:
                        raise e
                except ImportError:
                    raise e from None

            timings[choice] = timing

            # If a collective choice failed or timed out, skip the rest of the choices
            if is_collective and not math.isfinite(timing):
                log.warning(
                    "Choice %s failed or timed out during collective benchmarking. "
                    "Stopping further benchmarking to avoid NCCL corruption.",
                    getattr(choice, "name", "<unknown>"),
                )
                timings.update({c: float("inf") for c in choices if c not in timings})
                break

            # Skip remaining CUTLASS choices after first failure (#171094)
            if not math.isfinite(timing) and isinstance(choice, CUTLASSTemplateCaller):
                has_valid_fallback = any(
                    math.isfinite(t) and not isinstance(c, CUTLASSTemplateCaller)
                    for c, t in timings.items()
                )
                if has_valid_fallback:
                    log.warning(
                        "CUTLASS choice %s failed during benchmarking. "
                        "Skipping remaining CUTLASS choices to avoid CUDA context corruption.",
                        getattr(choice, "name", "<unknown>"),
                    )
                    for c in choices:
                        if c not in timings and isinstance(c, CUTLASSTemplateCaller):
                            timings[c] = float("inf")
                    break

        return timings