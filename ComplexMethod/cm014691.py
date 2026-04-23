def test_dynamic_shapes(self):
        from functools import partial

        n = 10

        gen_tensor = (
            lambda n: R(1, n),
            lambda n: R(n, n),
            lambda n: R(n, n).transpose(0, 1),
            lambda n: R(n + 1, n + 1, 2)[:n, n, 0],
            lambda n: R(n, n, 2)[:, :, 0],
            lambda n: R(n, n + 1, n + 2, n + 3).to(memory_format=torch.channels_last),
        )

        with texpr_enable_strategy([("DYNAMIC", 20)]):

            def foo(x, y, z):
                return torch.sigmoid(torch.tanh(x))

            foo.__disable_jit_function_caching__ = True

            def fi(x, y, z):
                return torch.tanh(x + y)

            fi.__disable_jit_function_caching__ = True

            def fum(x, y, z):
                return torch.tanh(x + y) + z

            fum.__disable_jit_function_caching__ = True

            funcs = [foo, fi, fum]
            with inline_fusion_groups():
                for device in self.devices:
                    I = partial(torch.randint, 0, 100, device=device)
                    R = partial(torch.randn, device=device)

                    for i, func in enumerate(funcs):
                        num_args = i + 1
                        for gen in gen_tensor:
                            inps = (gen(n), gen(n), gen(n))
                            func_s = torch.jit.trace(func, inps, check_trace=False)
                            torch._C._jit_pass_erase_shape_information(func_s.graph)
                            for _ in range(2):
                                x, y, z = gen(n), gen(n), gen(n)
                                func_s(x, y, z)

                            for _incr in range(3):
                                func_s(*[gen(n + 1) for _ in range(3)])

                            g = torch.jit.last_executed_optimized_graph()
                            torch._C._jit_pass_inline(g)
                            torch._C._jit_pass_dce(g)

                            # We should see only one optimized kernel
                            FileCheck().check_count(
                                "TensorExprDynamicGuard", 1, exactly=True
                            ).run(g)
                            self.assertEqual(func(*inps), func_s(*inps))

                    gen = gen_tensor[0]
                    inps = (gen(n), gen(n), gen(n))
                    foo_s = torch.jit.trace(foo, inps)
                    torch._C._jit_pass_erase_shape_information(foo_s.graph)
                    g_prev = None
                    for gen in gen_tensor:
                        for i in range(3):
                            foo_s(*[gen(n + i) for _ in range(3)])
                            inps = (gen(n), gen(n), gen(n))
                            self.assertEqual(foo_s(*inps), foo(*inps))
                    g = torch.jit.last_executed_optimized_graph()
                    torch._C._jit_pass_inline(g)
                    torch._C._jit_pass_dce(g)
                    FileCheck().check_count(
                        "TensorExprDynamicGuard", len(gen_tensor), exactly=True
                    ).run(g)