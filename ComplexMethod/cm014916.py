def test_number_math(self):
        ops_template = dedent('''
        def func():
            return {scalar1} {op} {scalar2}
        ''')
        ops = ['+', '-', '*', '%', '<', '<=', '>', '>=', '==', '!=', '//']
        funcs_template = dedent('''
        def func():
            return {func}({scalar1}, {scalar2})
        ''')
        funcs = ['min', 'max']
        scalars = ['7', '2', '3', '-3', '3.14', '0.125', '-0.5', '2.0', '-2.0']
        scalar_pairs = [(scalar1, scalar2) for scalar1 in scalars for scalar2 in scalars]

        def run_test(code):
            scope = {}
            execWrapper(code, globals(), scope)
            cu = torch.jit.CompilationUnit(code)

            self.assertEqual(cu.func(), scope['func']())

        for scalar1, scalar2 in scalar_pairs:
            for op in ops:
                code = ops_template.format(op=op, scalar1=scalar1, scalar2=scalar2)
                run_test(code)
            for func in funcs:
                code = funcs_template.format(func=func, scalar1=scalar1, scalar2=scalar2)
                run_test(code)

        # test Scalar overloads
        for scalar1, scalar2 in scalar_pairs:
            item1 = 'torch.tensor(' + scalar1 + ').item()'
            item2 = 'torch.tensor(' + scalar2 + ').item()'
            for op in ops:
                code = ops_template.format(op=op, scalar1=item1, scalar2=scalar2)
                run_test(code)
                code = ops_template.format(op=op, scalar1=scalar1, scalar2=item2)
                run_test(code)
                code = ops_template.format(op=op, scalar1=item1, scalar2=item2)
                run_test(code)
            for func in funcs:
                code = funcs_template.format(func=func, scalar1=item1, scalar2=scalar2)
                run_test(code)
                code = funcs_template.format(func=func, scalar1=scalar1, scalar2=item2)
                run_test(code)
                code = funcs_template.format(func=func, scalar1=item1, scalar2=item2)
                run_test(code)