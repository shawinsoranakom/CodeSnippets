def run_with_fake_mode_and_verify(fake_mode, match_results=True):
                def map_to_fake(e):
                    if isinstance(e, torch.Tensor):
                        return fake_mode.from_tensor(e)
                    else:
                        return e

                input = tree_map(map_to_fake, sample.input)
                args = tree_map(map_to_fake, sample.args)
                kwargs = tree_map(map_to_fake, sample.kwargs)

                try:
                    with context():
                        with fake_mode:
                            res_fake = op(input, *args, **kwargs)

                    if not match_results:
                        return

                    for fake_out, real_out in zip(
                        pytree.tree_leaves(res_fake), pytree.tree_leaves(res)
                    ):
                        if not isinstance(fake_out, torch.Tensor):
                            self.assertTrue(not isinstance(real_out, torch.Tensor))
                            self.assertEqual(fake_out, real_out)
                            continue

                        self.assertTrue(isinstance(fake_out, FakeTensor))
                        # if you see a shape exception here, you may need to add
                        # a `dynamic_output_shape` tag to an operator

                        if op.op not in [
                            torch.ops.aten._efficient_attention_forward,
                            torch.ops.aten._flash_attention_forward,
                        ]:
                            # prims/decomps must correctly model strides,
                            # see https://github.com/pytorch/pytorch/issues/78050#issuecomment-1253950325

                            # note: the excluded ops have intentionally incorrect device;
                            # see "Note [Seed and Offset]" (_meta_registrations.py)
                            prims.utils.compare_tensor_meta(fake_out, real_out, True)

                        if name not in aliasing_failures:
                            fake_aliasing = outputs_alias_inputs(
                                (input, args, kwargs), res_fake
                            )
                            real_aliasing = outputs_alias_inputs(
                                (sample.input, sample, args, sample.kwargs), res
                            )
                            self.assertEqual(fake_aliasing, real_aliasing)

                    self.assertTrue(
                        name not in dynamic_output_op_tests
                        and name not in data_dependent_op_tests
                    )

                except torch._subclasses.fake_tensor.UnsupportedFakeTensorException:
                    pass
                except torch._subclasses.fake_tensor.UnsupportedOperatorException:
                    pass
                except torch._subclasses.fake_tensor.DynamicOutputShapeException:
                    self.assertTrue(
                        name in dynamic_output_op_tests
                        or name in sometimes_dynamic_output_op_test
                    )
                    self.assertTrue(
                        fake_mode.shape_env is None
                        or not fake_mode.shape_env.allow_dynamic_output_shape_ops
                        or name not in supported_dynamic_output_op_tests
                    )
                except torch._subclasses.fake_tensor.DataDependentOutputException:
                    self.assertTrue(name in data_dependent_op_tests)