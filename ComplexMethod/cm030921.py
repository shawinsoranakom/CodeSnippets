def test_unconditional_jump_threading(self):

        def get_insts(lno1, lno2, op1, op2):
            return [
                       lbl2 := self.Label(),
                       ('LOAD_NAME', 0, 10),
                       ('POP_TOP', None, 10),
                       (op1, lbl1 := self.Label(), lno1),
                       ('LOAD_NAME', 1, 20),
                       lbl1,
                       (op2, lbl2, lno2),
                   ]

        for op1 in ('JUMP', 'JUMP_NO_INTERRUPT'):
            for op2 in ('JUMP', 'JUMP_NO_INTERRUPT'):
                # different lines
                lno1, lno2 = (4, 5)
                with self.subTest(lno = (lno1, lno2), ops = (op1, op2)):
                    insts = get_insts(lno1, lno2, op1, op2)
                    op = 'JUMP' if 'JUMP' in (op1, op2) else 'JUMP_NO_INTERRUPT'
                    expected_insts = [
                        ('LOAD_NAME', 0, 10),
                        ('POP_TOP', None, 10),
                        ('NOP', None, 4),
                        (op, 0, 5),
                    ]
                    self.cfg_optimization_test(insts, expected_insts, consts=list(range(5)))

                # Threading
                for lno1, lno2 in [(-1, -1), (-1, 5), (6, -1), (7, 7)]:
                    with self.subTest(lno = (lno1, lno2), ops = (op1, op2)):
                        insts = get_insts(lno1, lno2, op1, op2)
                        lno = lno1 if lno1 != -1 else lno2
                        if lno == -1:
                            lno = 10  # Propagated from the line before

                        op = 'JUMP' if 'JUMP' in (op1, op2) else 'JUMP_NO_INTERRUPT'
                        expected_insts = [
                            ('LOAD_NAME', 0, 10),
                            ('POP_TOP', None, 10),
                            (op, 0, lno),
                        ]
                        self.cfg_optimization_test(insts, expected_insts, consts=list(range(5)))