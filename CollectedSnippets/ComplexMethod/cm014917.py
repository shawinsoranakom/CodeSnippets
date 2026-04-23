def test_torch_tensor_as_tensor(self):
        tensor_template = dedent('''
        def func():
            li = {list_create}
            ten1 = torch.{tensor_op}(li {options})
            return ten1
        ''')

        lists = ["2.5", "4", "True", "False", "[2]", "[-.5]", "[False, True, False]", "[2, 2]", "(1, 1)",
                 "torch.jit.annotate(List[List[int]], [])",
                 "torch.jit.annotate(List[int], [])", "[2.5, 2.5]", "[[2], [2]]", "[[-.5], [2.2]]", "[[False], [True]]"]

        dtypes = ["", ", dtype=torch.float", ", dtype=torch.double", ", dtype=torch.half",
                  ", dtype=torch.uint8", ", dtype=torch.int8", ", dtype=torch.short",
                  ", dtype=torch.int", ", dtype=torch.long", ", dtype=torch.cfloat",
                  ", dtype=torch.cdouble"]

        ops = ['tensor', 'as_tensor']
        devices = ['', ", device='cpu'"]
        if RUN_CUDA:
            devices.append(", device='cuda'")

        option_pairs = [dtype + device for dtype in dtypes for device in devices]
        for op in ops:
            for li in lists:
                for option in option_pairs:
                    # tensor from empty list is type float in python and annotated type in torchscript
                    if "annotate" in li and "dtype" not in option:
                        continue
                    # Skip unsigned tensor initialization for signed values on 3.10
                    if "torch.uint8" in option and "-" in li:
                        continue
                    code = tensor_template.format(list_create=li, tensor_op=op, options=option)
                    scope = {}
                    exec(code, globals(), scope)
                    cu = torch.jit.CompilationUnit(code)
                    t1 = cu.func()
                    t2 = scope['func']()
                    if t1.dtype == torch.float16:  # equality NYI for half tensor
                        self.assertTrue(str(t1) == str(t2))
                    else:
                        self.assertEqual(t1, t2)
                    self.assertEqual(t1.dtype, t2.dtype)
                    self.assertEqual(t1.device, t2.device)

        def test_as_tensor_tensor_input(input):
            # type: (Tensor) -> Tuple[Tensor, Tensor, Tensor]
            return torch.as_tensor(input, dtype=torch.cfloat), torch.as_tensor(input, dtype=torch.float), \
                torch.as_tensor(input, dtype=torch.int32)

        inp = torch.randn(3, 4, dtype=torch.cfloat)
        self.checkScript(test_as_tensor_tensor_input, (inp,))