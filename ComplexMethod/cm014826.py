def test_method(self, fn, first_type, second_type):
        if first_type == "float":
            # TODO: Hmm, this looks like we skip all floats
            self.skipTest(f"{fn} is not a float magic method")

        if (
            first_type == "int" or second_type == "int"
        ) and fn in sym_node.only_float_magic_methods:
            self.skipTest(f"{fn} is not an int method")

        if second_type == "float" and fn == "mod":
            self.skipTest(f"{fn} only handles int")

        if fn in sym_node.bitwise_ops and (first_type != "int" or second_type != "int"):
            self.skipTest(f"{fn} is a bitwise op, only handles int")

        is_unary_fn = fn in sym_node.unary_methods or fn == "round"
        # Second argument is ignored for unary function. So only run for one type
        if is_unary_fn and second_type == "float":
            self.skipTest(f"{fn} is unary and already tested")

        if fn in sym_node.bool_magic_methods:
            self.skipTest(f"{fn} is bool")

        # Only floats here since these will be converted to int if necessary.
        # We also ignore complex and bool.
        values = (
            0.0,
            1.0,
            0.5 if fn in ("sym_acos", "sym_asin") else 2.5,  # avoid math domain error
        )

        neg_values = tuple(-x for x in values)

        for inp1, inp2 in itertools.chain(
            itertools.product(values, values),
            itertools.product(values, neg_values),
            itertools.product(neg_values, values),
            itertools.product(neg_values, neg_values),
        ):
            if first_type == "int":
                inp1 = int(inp1)
            if second_type == "int":
                inp2 = int(inp2)

            shape_env = ShapeEnv()

            self._do_test(fn, inp1, inp2, shape_env, is_unary_fn)