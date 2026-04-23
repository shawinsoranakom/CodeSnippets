def test_underscores(self):
        # check underscores
        for lit in VALID_UNDERSCORE_LITERALS:
            if not any(ch in lit for ch in 'xXoObB'):
                self.assertEqual(complex(lit), eval(lit))
                self.assertEqual(complex(lit), complex(lit.replace('_', '')))
        for lit in INVALID_UNDERSCORE_LITERALS:
            if lit in ('0_7', '09_99'):  # octals are not recognized here
                continue
            if not any(ch in lit for ch in 'xXoObB'):
                self.assertRaises(ValueError, complex, lit)