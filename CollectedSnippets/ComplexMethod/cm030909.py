def test_return_in_with_positions(self):
        # See gh-98442
        def f():
            with xyz:
                1
                2
                3
                4
                return R

        # All instructions should have locations on a single line
        for instr in dis.get_instructions(f):
            start_line, end_line, _, _ = instr.positions
            self.assertEqual(start_line, end_line)

        # Expect four `LOAD_CONST None` instructions:
        # three for the no-exception __exit__ call, and one for the return.
        # They should all have the locations of the context manager ('xyz').

        load_none = [instr for instr in dis.get_instructions(f) if
                     instr.opname == 'LOAD_CONST' and instr.argval is None]
        return_value = [instr for instr in dis.get_instructions(f) if
                        instr.opname == 'RETURN_VALUE']

        self.assertEqual(len(load_none), 4)
        self.assertEqual(len(return_value), 2)
        for instr in load_none + return_value:
            start_line, end_line, start_col, end_col = instr.positions
            self.assertEqual(start_line, f.__code__.co_firstlineno + 1)
            self.assertEqual(end_line, f.__code__.co_firstlineno + 1)
            self.assertEqual(start_col, 17)
            self.assertEqual(end_col, 20)