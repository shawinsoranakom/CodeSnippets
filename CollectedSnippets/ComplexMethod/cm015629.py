def test_symbool_guards(
            f, size_tests, exp_graph, exp_guard_code, exp_shape_env_guards
        ):
            shape_env = ShapeEnv()
            with fake_tensor.FakeTensorMode(
                shape_env=shape_env,
            ) as fake_mode:
                fake_x = fake_mode.from_tensor(
                    x,
                    symbolic_context=StatelessSymbolicContext(
                        dynamic_sizes=[DimDynamic.DYNAMIC for _ in range(x.dim())],
                    ),
                )
                for i, size in enumerate(size_tests):
                    pred = fake_x.size(0) == size
                    gm, guards = torch._dynamo.export(f)(pred, x)
                    actual = normalize_gm(gm.print_readable(print_output=False))
                    # TODO: This is naughty, EXPECTTEST_ACCEPT=1 doesn't work
                    self.assertExpectedInline(actual, exp_graph[i].format(size=size))
                    dynamo_shape_env_guards = [
                        guard
                        for guard in guards
                        if guard.guard_types is not None
                        and "SHAPE_ENV" in guard.guard_types
                    ]
                    self.assertEqual(len(dynamo_shape_env_guards), 1)
                    guard_code_on_predicate = [
                        code
                        for code in dynamo_shape_env_guards[0].code_list
                        if "L['pred']" in code
                    ]
                    self.assertEqual(guard_code_on_predicate, exp_guard_code[i])
                    outter_shape_env_guards = [
                        str(guard.expr) for guard in shape_env.guards
                    ]
                    self.assertEqual(outter_shape_env_guards, exp_shape_env_guards[i])