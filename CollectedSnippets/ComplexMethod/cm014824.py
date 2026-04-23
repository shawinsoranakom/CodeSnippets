def test_arith_ops(self):
        shape_env = ShapeEnv()
        symints = []
        for i in range(2, 5):
            symints.append((i, create_symint(shape_env, i)))

        ops = [
            operator.add,
            operator.sub,
            operator.floordiv,
            operator.mul,
            operator.mod,
        ]

        for op in ops:
            for args in itertools.permutations(symints, 2):
                if not isinstance(args[0][1], int) and (
                    (op != operator.mod or op != operator.floordiv) and args[1][0] != 0
                ):
                    self.assertTrue(
                        op(args[0][1], args[1][1]) == op(args[0][0], args[1][0])
                    )