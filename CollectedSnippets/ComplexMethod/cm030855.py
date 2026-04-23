def test_enter_scope_two_events(self):
        try:
            yield_counter = CounterWithDisable()
            unwind_counter = CounterWithDisable()
            sys.monitoring.register_callback(TEST_TOOL, E.PY_YIELD, yield_counter)
            sys.monitoring.register_callback(TEST_TOOL, E.PY_UNWIND, unwind_counter)
            sys.monitoring.set_events(TEST_TOOL, E.PY_YIELD | E.PY_UNWIND)

            yield_value = int(math.log2(E.PY_YIELD))
            unwind_value = int(math.log2(E.PY_UNWIND))
            cl = _testcapi.CodeLike(2)
            common_args = (cl, 0)
            with self.Scope(cl, yield_value, unwind_value):
                yield_counter.count = 0
                unwind_counter.count = 0

                _testcapi.fire_event_py_unwind(*common_args, ValueError(42))
                assert(yield_counter.count == 0)
                assert(unwind_counter.count == 1)

                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 1)
                assert(unwind_counter.count == 1)

                yield_counter.disable = True
                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 2)
                assert(unwind_counter.count == 1)

                _testcapi.fire_event_py_yield(*common_args, ValueError(42))
                assert(yield_counter.count == 2)
                assert(unwind_counter.count == 1)

        finally:
            sys.monitoring.set_events(TEST_TOOL, 0)