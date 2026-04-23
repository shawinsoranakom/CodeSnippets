def test_runtime_checks(self):
        class Model(torch.nn.Module):
            def forward(self, inputs):
                return list(inputs.values())

        inputs = {}
        dtypes = [
            torch.float16,
            torch.float32,
            torch.bool,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
            torch.uint8,
        ]

        if not TEST_MPS:
            dtypes.append(torch.float64)
        if SM80OrLater:
            dtypes.append(torch.bfloat16)

        for dtype in dtypes:
            inputs[f"x_{str(dtype)}"] = torch.ones(
                4, 8, 10, dtype=dtype, device=self.device
            )

        dim0 = Dim("s0", min=2, max=1024)
        dim1 = Dim("s1", min=2, max=512)
        dim2 = Dim("s2", min=2, max=128)
        dynamic_shapes = {
            "x_torch.float16": {0: dim0},
            "x_torch.float32": {0: dim0},
            "x_torch.bool": {1: dim1},
            "x_torch.int8": {1: dim1},
            "x_torch.int16": {},
            "x_torch.int32": {2: dim2},
            "x_torch.int64": {2: dim2},
            "x_torch.uint8": {2: dim2},
        }
        if not TEST_MPS:
            dynamic_shapes["x_torch.float64"] = {0: dim0}
        if SM80OrLater:
            dynamic_shapes["x_torch.bfloat16"] = {1: dim1}

        m = Model()
        inputs = (inputs,)
        dynamic_shapes = (dynamic_shapes,)
        with torch.no_grad():
            so_path = AOTIRunnerUtil.legacy_compile(
                m, inputs, dynamic_shapes=dynamic_shapes
            )

        # Expected results for the following checks:
        # ("unmatched dtype", "unmatched dim value at", "dim value is too", "unmatched stride value at")
        if SM80OrLater:
            # 10 dynamic dims
            expected_results = (10, 21, 18, 21)
        elif TEST_MPS:
            # 8 dynamic dims
            expected_results = (8, 17, 14, 16)
        else:
            # 9 dynamic dims
            expected_results = (9, 19, 16, 19)

        with open(os.path.splitext(so_path)[0] + ".cpp") as cpp:
            src_code = cpp.read()
            FileCheck().check_count(
                "unmatched dtype",
                expected_results[0],
                exactly=True,
            ).run(src_code)
            FileCheck().check_count(
                "unmatched dim value at",
                expected_results[1],
                exactly=True,
            ).run(src_code)
            FileCheck().check_count(
                "dim value is too",
                expected_results[2],
                exactly=True,
            ).run(src_code)
            FileCheck().check_count(
                "unmatched stride value at",
                expected_results[3],
                exactly=True,
            ).run(src_code)

        self.check_model(m, inputs)