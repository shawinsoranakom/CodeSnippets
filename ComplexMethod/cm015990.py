def test_record_function_fast(self):
        x, y = (torch.rand((4, 4)) for _ in range(2))
        with profile(record_shapes=True) as p:
            for _ in range(4):
                # Test first with no optional args
                with torch._C._profiler._RecordFunctionFast("add_test_fast_rf1"):
                    x.add(y)

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf1"]), 4
        )
        for e in p.events():
            if e.name == "add_test_fast_rf1":
                self.assertTrue(e.input_shapes == [])
                self.assertTrue(e.kwinputs == {})
        with profile(record_shapes=True) as p:
            # add optional args
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_fast_rf2", [x, y], {"stream": 0, "grid": "lambda x : x + 1"}
            )
            for _ in range(4):
                with cm:
                    x.add(y)

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf2"]), 4
        )

        for e in p.events():
            if e.name == "add_test_fast_rf2":
                self.assertTrue(e.input_shapes == [[4, 4], [4, 4]])
                self.assertTrue(e.kwinputs == {"stream": 0, "grid": "lambda x : x + 1"})

        with profile(record_shapes=True) as p:
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_fast_rf3", input_values=["hi"], keyword_values={"hi": "hello"}
            )
            for _ in range(4):
                try:
                    with cm:
                        x.add(y)
                        raise ValueError
                        x.relu()
                except ValueError:
                    pass

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf3"]), 4
        )
        self.assertFalse(any((e.name and "relu" in e.name) for e in p.events()))

        for e in p.events():
            if e.name == "add_test_fast_rf3":
                self.assertTrue(e.input_shapes == [[]])

        with profile() as p:
            for _ in range(4):
                with torch._C._profiler._RecordFunctionFast(
                    "add_test_fast_rf4", [x, y]
                ):
                    x.add(y)
                    with torch._C._profiler._RecordFunctionFast("add_test_fast_rf5"):
                        x.relu()

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf4"]), 4
        )

        for e in p.events():
            if e.name == "add_test_fast_rf4":
                self.assertTrue(e.input_shapes == [])

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf5"]), 4
        )

        with profile(record_shapes=True) as p:
            # test optional args with tuple
            cm = torch._C._profiler._RecordFunctionFast(
                "add_test_fast_rf6",
                (
                    x,
                    y,
                ),
            )
            for _ in range(4):
                with cm:
                    x.add(y)

        self.assertGreaterEqual(
            len([e for e in p.events() if e.name == "add_test_fast_rf6"]), 4
        )

        for e in p.events():
            if e.name == "add_test_fast_rf6":
                self.assertTrue(e.input_shapes == [[4, 4], [4, 4]])