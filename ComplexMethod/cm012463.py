def gen_loop_with_reduction(
                _loop_nest: LoopNest, depth: int = 0, in_reduction=False
            ):
                kernel = _loop_nest.get_kernel()
                assert _loop_nest.loops
                loop = _loop_nest.loops[depth]
                with contextlib.ExitStack() as stack_outer:
                    if loop.is_reduction and not in_reduction:
                        reduction_prefix = get_reduction_prefix_suffix(
                            kernel, loop.parallel, is_suffix=False
                        )
                        if reduction_prefix:
                            stack_outer.enter_context(code.indent())
                        code.splice(reduction_prefix)
                    if is_reduction_loop and loop.parallel:
                        worksharing.parallel(threads)
                        if kernel.local_reduction_init:
                            assert kernel.local_reduction_stores
                            code.splice(kernel.local_reduction_init)

                    gen_loop_at(_loop_nest, depth)

                    if is_reduction_loop and loop.parallel:
                        if kernel.local_reduction_stores:
                            code.splice(kernel.local_reduction_stores)
                        worksharing.close()
                    if loop.is_reduction and not in_reduction:
                        code.splice(
                            get_reduction_prefix_suffix(
                                kernel, loop.parallel, is_suffix=True
                            )
                        )