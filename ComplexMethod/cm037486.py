def import_kernels(cls) -> None:
        if Platform.get_cpu_architecture() in (CpuArchEnum.X86,):
            # Note: The lib name is _C_AVX2/AVX512, but the module name is _C.
            # This will cause a exception "dynamic module does define
            # module export function". But the library is imported
            # successfully. So ignore the exception for now, until we find
            # a solution.
            ignored_msg = "dynamic module does not define module export function"
            if torch.cpu._is_avx512_supported():
                if torch.cpu._is_avx512_bf16_supported():
                    try:
                        import vllm._C  # noqa: F401
                    except ImportError as e:
                        logger.warning("Failed to import from vllm._C: %r", e)
                else:
                    try:
                        import vllm._C_AVX512  # noqa: F401
                    except ImportError as e:
                        if ignored_msg not in e.msg:
                            logger.warning(
                                "Failed to import from vllm._C_AVX512: %r", e
                            )
            else:
                try:
                    import vllm._C_AVX2  # noqa: F401
                except ImportError as e:
                    if ignored_msg not in e.msg:
                        logger.warning("Failed to import from vllm._C_AVX2: %r", e)
        else:
            try:
                import vllm._C  # noqa: F401
            except ImportError as e:
                logger.warning("Failed to import from vllm._C: %r", e)