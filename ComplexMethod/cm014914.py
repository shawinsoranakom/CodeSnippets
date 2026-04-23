def test_constant_insertion(self):
        funcs_template = dedent('''
        def func():
            return {constant_constructor}
        ''')

        # constants: primitives: int, double, bool, str, lists of primitives,
        # and tuples
        def check_constant(constant_constructor):
            scope = {}
            funcs_str = funcs_template.format(constant_constructor=constant_constructor)
            execWrapper(funcs_str, globals(), scope)
            cu = torch.jit.CompilationUnit(funcs_str)
            f_script = cu.func
            self.run_pass('constant_propagation', f_script.graph)
            FileCheck().check_count("prim::Constant", 1, exactly=True).run(f_script.graph)
            self.assertEqual(scope['func'](), f_script())
            imported = self.getExportImportCopy(f_script)
            self.assertEqual(imported(), f_script())

        constants = ["None", "-.5", "0", "1", "True", "False", "''", "'a'", "'b'", "torch.tensor(1)",
                     "[True, False]", "[0., .5]", "[torch.tensor(4), torch.tensor(2)]", "[0, 1]", "['0', '1']",
                     "[True, None]", "[.5, None, .2]"]

        for type in ["Tensor", "str", "int", "float", "bool"]:
            constants.append("torch.jit.annotate(List[ " + type + "], [])")

        for constant in constants:
            check_constant(constant)

        for key_type in ["str", "int", "float"]:
            for value_type in ["Tensor", "bool", "str", "int", "float"]:
                check_constant("torch.jit.annotate(Dict[ " + key_type + ", " + value_type + "], {})")
                check_constant("torch.jit.annotate(Dict[ " + key_type + ", Optional[" + value_type + "]], {})")

        for i in range(len(constants)):
            for j in range(i + 1, len(constants)):
                tup_constant = constants[i] + ", " + constants[j]
                check_constant(tup_constant)

        dict_constants = []
        for i in range(len(constants)):
            # check_constant constructs the second dict with another Tensor
            # which fails the comparison
            if not isinstance(eval(constants[i]), (str, int, float)):
                continue
            for j in range(len(constants)):
                dict_constant = "{ " + constants[i] + ": " + constants[j] + "}"
                check_constant(dict_constant)
                dict_constants.append(dict_constant)
        constants = constants + dict_constants

        # testing node hashing
        funcs_template = dedent('''
        def func():
            print({constant_constructor})
        ''')
        single_elem_tuples = ("(" + x + ",)" for x in constants)
        input_arg = ", ".join(single_elem_tuples)
        scope = {}
        funcs_str = funcs_template.format(constant_constructor=input_arg)
        execWrapper(funcs_str, globals(), scope)
        cu = torch.jit.CompilationUnit(funcs_str)
        f_script = cu.func
        self.run_pass('constant_propagation', f_script.graph)
        # prim::None return adds one constant
        self.assertEqual(len(constants) + 1, str(f_script.graph).count("prim::Constant"))
        self.run_pass('cse', f_script.graph)
        # node hashing correctly working, no CSE occurs
        self.assertEqual(len(constants) + 1, str(f_script.graph).count("prim::Constant"))

        funcs_template = dedent('''
        def func():
            a = {constant_constructor}
            print(a)
            b = {constant_constructor}
            print(b)
        ''')

        # generate dicts with built-in types (excluding torch.Tensor)
        xprod = itertools.product(constants, constants)

        # test that equal tuples and dicts correctly work with node hashing
        for tup in ("(" + x + ",)" for x in constants):
            funcs_str = funcs_template.format(constant_constructor=tup)
            scope = {}
            execWrapper(funcs_str, globals(), scope)
            cu = torch.jit.CompilationUnit(funcs_str)
            f_script = cu.func
            self.run_pass('constant_propagation_immutable_types', f_script.graph)
            num_constants = str(f_script.graph).count("prim::Constant")
            self.run_pass('cse', f_script.graph)
            FileCheck().check_count("prim::Constant", num_constants, exactly=True).run(f_script.graph)