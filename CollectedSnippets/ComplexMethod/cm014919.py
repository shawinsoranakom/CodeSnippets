def _test_binary_op_shape(self, ops, input_dims=1):

        dtypes = [torch.float32, torch.float64, torch.int64, torch.int32, torch.bool]

        if input_dims == 0:
            shape = '1'
        else:
            shape = '[' + ('1,' * 4) + ']'
            for _ in range(1, input_dims):
                shape = '[' + ",".join([shape] * 4) + ']'

        template = dedent('''
        def func():
            arg1 = {}
            arg2 = {}
            return torch.{}(arg1, arg2)
        ''')

        args = []
        for dtype in dtypes:
            args = args + [f"torch.tensor({shape}, dtype={dtype})"]
        args = args + [1, 1.5]

        def isBool(arg):
            return type(arg) is bool or (type(arg) is str and "torch.bool" in arg)

        for op in ops:
            for first_arg in args:
                for second_arg in args:
                    # subtract not supported for bool
                    if (op == 'sub' or op == 'div') and (isBool(first_arg) or isBool(second_arg)):
                        continue
                    # div is not implemented correctly for mixed-type or int params
                    if (op == 'div' and (type(first_arg) is not type(second_arg) or
                       isinstance(first_arg, int) or
                       (isinstance(first_arg, str) and 'int' in first_arg))):
                        continue
                    return_line = f"torch.{op}({first_arg}, {second_arg})"
                    # uncomment for debugging a failed test:
                    # print("testing {}".format(return_line))
                    code = template.format(first_arg, second_arg, op)
                    scope = {}
                    exec(code, globals(), scope)
                    non_jit_result = scope['func']()

                    cu = torch.jit.CompilationUnit(code)
                    graph = cu.func.graph
                    torch._C._jit_pass_complete_shape_analysis(graph, (), False)
                    # use dim=-1 to represent a python/jit scalar.
                    dim = -1 if type(first_arg) is not str and type(second_arg) is not str else non_jit_result.dim()
                    dtype = non_jit_result.dtype
                    # jit only supports int/float scalars.
                    if dim < 0:
                        if dtype == torch.int64:
                            dtype = torch.int32
                        if dtype == torch.float64:
                            dtype = torch.float32
                    expect = self._dtype_to_expect(dtype, dim)
                    jit_output = next(graph.outputs())

                    check = FileCheck()
                    check.check(expect).run(str(jit_output))