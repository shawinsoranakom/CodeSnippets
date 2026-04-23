def test_co_positions_with_lots_of_caches(self):
        def roots(a, b, c):
            d = b**2 - 4 * a * c
            yield (-b - cmath.sqrt(d)) / (2 * a)
            if d:
                yield (-b + cmath.sqrt(d)) / (2 * a)
        code = roots.__code__
        ops = code.co_code[::2]
        cache_opcode = opcode.opmap["CACHE"]
        caches = sum(op == cache_opcode for op in ops)
        non_caches = len(ops) - caches
        # Make sure we have "lots of caches". If not, roots should be changed:
        assert 1 / 3 <= caches / non_caches, "this test needs more caches!"
        for show_caches in (False, True):
            for adaptive in (False, True):
                with self.subTest(f"{adaptive=}, {show_caches=}"):
                    co_positions = [
                        positions
                        for op, positions in zip(ops, code.co_positions(), strict=True)
                        if show_caches or op != cache_opcode
                    ]
                    dis_positions = [
                        None if instruction.positions is None else (
                            instruction.positions.lineno,
                            instruction.positions.end_lineno,
                            instruction.positions.col_offset,
                            instruction.positions.end_col_offset,
                        )
                        for instruction in _unroll_caches_as_Instructions(dis.get_instructions(
                            code, adaptive=adaptive, show_caches=show_caches
                        ), show_caches=show_caches)
                    ]
                    self.assertEqual(co_positions, dis_positions)