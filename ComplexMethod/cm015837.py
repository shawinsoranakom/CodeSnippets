def _run_test(
        self, model, inputs, device, dynamic=False, num_counters=1, autograd=False
    ):
        import torch.utils._pytree as pytree

        cnt = torch._dynamo.testing.CompileCounterWithBackend("inductor")
        import copy

        if not autograd:
            for p in model.parameters():
                p.requires_grad_(False)

        compiled_model = copy.deepcopy(model)
        compiled_fn = torch.compile(backend=cnt, fullgraph=True)(compiled_model)

        inputs = pytree.tree_map(lambda t: t.to(device=device), inputs)
        input_sets = [inputs]

        def mark_first_dim_dyn(inp):
            torch._dynamo.mark_dynamic(inp, 0)

        if dynamic:

            def tile_fn(inp):
                # tile every first dim 5x
                tiling = [5] + [1] * (inp.ndim - 1)
                t = torch.tile(inp, tiling)
                return t

            larger_inputs = pytree.tree_map(tile_fn, inputs)
            input_sets.append(larger_inputs)

        for inputs in input_sets:
            flat_inputs, inp_spec = pytree.tree_flatten(inputs)
            for flat_inputs_with_counters in prepend_counters(
                flat_inputs, num_counters
            ):
                counters, flat = (
                    flat_inputs_with_counters[:num_counters],
                    flat_inputs_with_counters[num_counters:],
                )
                unflat_inputs = pytree.tree_unflatten(flat, inp_spec)
                inputs_with_counters = counters + unflat_inputs

                def process_inputs(inp):
                    inp = inp.clone()
                    if dynamic:
                        mark_first_dim_dyn(inp)

                    if autograd and inp.dtype.is_floating_point:
                        inp.requires_grad_(True)
                    return inp

                cloned_inputs = pytree.tree_map(process_inputs, inputs_with_counters)
                cloned_inputs2 = pytree.tree_map(process_inputs, inputs_with_counters)

                result = model(*cloned_inputs)
                result_compiled = compiled_fn(*cloned_inputs2)
                # inputs must not be mutated
                torch.testing.assert_close(cloned_inputs, inputs_with_counters)
                torch.testing.assert_close(
                    result, result_compiled, atol=1e-4, rtol=1e-4
                )

                if autograd and any(
                    pytree.tree_map_only(
                        torch.Tensor, lambda t: t.requires_grad, cloned_inputs
                    )
                ):
                    result_loss = loss_fn(pytree.tree_flatten(result)[0])
                    compiled_loss = loss_fn(pytree.tree_flatten(result_compiled)[0])
                    self.assertTrue(
                        not torch.isnan(result_loss) and not torch.isinf(compiled_loss)
                    )
                    self.assertTrue(
                        not torch.isnan(compiled_loss)
                        and not torch.isinf(compiled_loss)
                    )

                    self.assertEqual(result_loss, compiled_loss)

                    result_loss.backward()
                    compiled_loss.backward()

                    model_parameters = dict(model.named_parameters())
                    compiled_parameters = dict(compiled_model.named_parameters())
                    for name, param in model_parameters.items():
                        self.assertEqual(param, compiled_parameters[name])
                        self.assertEqual(
                            param.grad,
                            compiled_parameters[name].grad,
                            atol=1e-4,
                            rtol=1e-4,
                        )

                    for inp1, inp2 in zip(
                        pytree.tree_flatten(cloned_inputs)[0],
                        pytree.tree_flatten(cloned_inputs2)[0],
                    ):
                        if inp1.requires_grad:
                            self.assertEqual(
                                inp1.grad,
                                inp2.grad,
                                atol=1e-4,
                                rtol=1e-4,
                            )

        self.assertEqual(cnt.frame_count, 1, "only one compilation expected")