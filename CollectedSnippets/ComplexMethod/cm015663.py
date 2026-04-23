def test_do_not_skip_side_effects(self):
        # https://github.com/pytorch/pytorch/issues/110765

        # By invoking torch.compiler.is_compiling(),
        # there may be side-effects inconsistent with eager when
        # compiling. Thus we force dynamo to commit the graph,
        # even if it does not perform any tensor operation
        global _variable, _variable_2

        for mode in range(1, 7):
            torch._dynamo.reset()

            _variable = 0
            _variable_2 = 0

            mod = MyModule(mode=mode)
            model = torch.compile(mod, backend="eager", fullgraph=mode != 6)
            if _variable != 0:
                raise AssertionError(f"Expected _variable 0, got {_variable}")
            if _variable_2 != 0:
                raise AssertionError(f"Expected _variable_2 0, got {_variable_2}")

            model(torch.tensor([1]))
            if _variable != 1:
                raise AssertionError(f"Expected _variable 1, got {_variable}")
            if _variable_2 != 0:
                raise AssertionError(f"Expected _variable_2 0, got {_variable_2}")

            model(torch.tensor([1]))
            if _variable != 2:
                raise AssertionError(f"Expected _variable 2, got {_variable}")
            if _variable_2 != 0:
                raise AssertionError(f"Expected _variable_2 0, got {_variable_2}")