def test_recompile_on_global_state_change(self):
        last_state = []
        cnt = 0

        def my_compiler(gm, _):
            nonlocal cnt
            cnt += 1
            state = read_state()

            def inner(*args):
                last_state[:] = state
                return gm(*args)

            return inner

        def read_state():
            return [
                torch.is_grad_enabled(),
                torch.are_deterministic_algorithms_enabled(),
                torch._C._get_cublas_allow_tf32(),
            ]

        def write_state(state):
            torch.set_grad_enabled(state[0])
            torch.use_deterministic_algorithms(state[1])
            torch._C._set_cublas_allow_tf32(state[2])

        @torch.compile(backend=my_compiler)
        def fn(x):
            return x + 1

        initial_state = read_state()
        y = torch.randn(10)
        try:
            for round in range(3):
                for i in range(len(initial_state)):
                    new_state = [False] * len(initial_state)
                    new_state[i] = True
                    write_state(new_state)
                    if read_state() != new_state:
                        raise AssertionError(f"Expected read_state() == {new_state}")
                    last_state.clear()
                    fn(y)
                    if last_state != new_state:
                        raise AssertionError(f"Expected last_state == {new_state}")
                    if round == 0:
                        if cnt != i + 1:
                            raise AssertionError(f"Expected cnt == {i + 1}, got {cnt}")
                    else:
                        if cnt != len(initial_state):
                            raise AssertionError(
                                f"Expected cnt == {len(initial_state)}, got {cnt}"
                            )
        finally:
            write_state(initial_state)