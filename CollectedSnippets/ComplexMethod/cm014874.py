def test_scatter_namedtuple(self):
        # tests ability to scatter namedtuples and retrieve a list where each
        # element is of the expected namedtuple type.
        fields = ("a", "b")
        TestNamedTupleInput_0 = collections.namedtuple("NamedTuple", fields)
        num_gpus = torch.cuda.device_count()
        a = torch.rand(num_gpus * 2, device=0)
        b = torch.rand(num_gpus * 2, device=0)
        a_tensors_for_gpu = [a[2 * i : 2 * i + 2].to(i) for i in range(num_gpus)]
        b_tensors_for_gpu = [b[2 * i : 2 * i + 2].to(i) for i in range(num_gpus)]

        inp = TestNamedTupleInput_0(a, b)
        target_gpus = [torch.device(i) for i in range(num_gpus)]
        scatter_out = scatter_gather.scatter(inp, target_gpus)

        for i, x in enumerate(scatter_out):
            self.assertTrue(isinstance(x, type(inp)))
            self.assertEqual(x._fields, fields)
            expected_a = a_tensors_for_gpu[i]
            expected_b = b_tensors_for_gpu[i]
            self.assertEqual(expected_a, x.a)
            self.assertEqual(expected_b, x.b)

        class TestNamedTupleInput_1(NamedTuple):
            a: torch.tensor
            b: torch.tensor

        a = torch.rand(num_gpus * 2, device=0)
        b = torch.rand(num_gpus * 2, device=0)
        a_tensors_for_gpu = [a[2 * i : 2 * i + 2].to(i) for i in range(num_gpus)]
        b_tensors_for_gpu = [b[2 * i : 2 * i + 2].to(i) for i in range(num_gpus)]
        inp = TestNamedTupleInput_1(a, b)

        scatter_out = scatter_gather.scatter(inp, target_gpus)
        for i, x in enumerate(scatter_out):
            self.assertTrue(isinstance(x, type(inp)))
            self.assertEqual(x._fields, fields)
            expected_a = a_tensors_for_gpu[i]
            expected_b = b_tensors_for_gpu[i]
            self.assertEqual(expected_a, x.a)
            self.assertEqual(expected_b, x.b)