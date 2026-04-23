def _test_dtype_op_shape(self, ops, args, input_dims=1):
        if input_dims < 1:
            raise RuntimeError("input dims must be at least 1")
        dtypes = [torch.float32, torch.float64, torch.int64, torch.int32]
        str_args = ', '.join([str(arg) for arg in args]) + (', ' if len(args) else '')
        tensor_data = ('[' * input_dims) + '1, 2, 3' + (input_dims * ']')
        template = dedent('''
        def func():
            return {return_line}
        ''')

        for op in ops:
            for dtype in (dtypes + [None]):
                for tensor_type in dtypes:
                    # a couple of ops aren't implemented for non-floating types
                    if not tensor_type.is_floating_point or (dtype is not None and not dtype.is_floating_point):
                        if op in ['mean', 'softmax', 'log_softmax']:
                            continue
                    return_line = f"torch.tensor({tensor_data}, dtype={tensor_type}).{op}({str_args}dtype={dtype})"
                    # uncomment for debugging a failed test:
                    # print("testing {}".format(return_line))
                    code = template.format(return_line=return_line)
                    scope = {}
                    exec(code, globals(), scope)
                    cu = torch.jit.CompilationUnit(code)
                    graph = cu.func.graph
                    torch._C._jit_pass_complete_shape_analysis(graph, (), False)
                    input_array = [1, 2, 3]
                    for _ in range(1, input_dims):
                        input_array = [input_array]
                    t = torch.tensor(input_array, dtype=tensor_type)
                    attr = getattr(t, op)
                    kwargs = {'dtype': dtype}
                    result = attr(*args, **kwargs)
                    expect = self._dtype_to_expect(result.dtype, result.dim())
                    FileCheck().check("aten::tensor").check(expect).run(graph)