def test_binary_ref_range(self, fn):
        # TODO: bring back sympy.oo testing for float unary fns
        vals = LESS_CONSTANTS
        for a, b in itertools.product(generate_range(vals), repeat=2):
            # don't attempt pow on exponents that are too large (but oo is OK)
            if fn == "pow" and b.upper > 4 and b.upper != sympy.oo:
                continue
            with self.subTest(a=a, b=b):
                for a0, b0 in itertools.product(LESS_CONSTANTS, repeat=2):
                    if a0 not in a or b0 not in b:
                        continue
                    if not valid_binary(fn, a0, b0):
                        continue
                    with self.subTest(a0=a0, b0=b0):
                        ref_r = getattr(ValueRangeAnalysis, fn)(a, b)
                        r = getattr(ReferenceAnalysis, fn)(
                            sympy.Integer(a0), sympy.Integer(b0)
                        )
                        if r.is_finite:
                            self.assertIn(r, ref_r)