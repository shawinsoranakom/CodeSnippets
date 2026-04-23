def test_range(self):
        check = self.check_match
        tescases = string.ascii_lowercase + string.digits + string.punctuation
        for c in tescases:
            check(c, '[b-d]', c in 'bcd')
            check(c, '[!b-d]', c not in 'bcd')
            check(c, '[b-dx-z]', c in 'bcdxyz')
            check(c, '[!b-dx-z]', c not in 'bcdxyz')
        # Case insensitive.
        for c in tescases:
            check(c, '[B-D]', (c in 'bcd') and IGNORECASE)
            check(c, '[!B-D]', (c not in 'bcd') or not IGNORECASE)
        for c in string.ascii_uppercase:
            check(c, '[b-d]', (c in 'BCD') and IGNORECASE)
            check(c, '[!b-d]', (c not in 'BCD') or not IGNORECASE)
        # Upper bound == lower bound.
        for c in tescases:
            check(c, '[b-b]', c == 'b')
        # Special cases.
        for c in tescases:
            check(c, '[!-#]', c not in '-#')
            check(c, '[!--.]', c not in '-.')
            check(c, '[^-`]', c in '^_`')
            if not (NORMSEP and c == '/'):
                check(c, '[[-^]', c in r'[\]^')
                check(c, r'[\-^]', c in r'\]^')
            check(c, '[b-]', c in '-b')
            check(c, '[!b-]', c not in '-b')
            check(c, '[-b]', c in '-b')
            check(c, '[!-b]', c not in '-b')
            check(c, '[-]', c in '-')
            check(c, '[!-]', c not in '-')
        # Upper bound is less that lower bound: error in RE.
        for c in tescases:
            check(c, '[d-b]', False)
            check(c, '[!d-b]', True)
            check(c, '[d-bx-z]', c in 'xyz')
            check(c, '[!d-bx-z]', c not in 'xyz')
            check(c, '[d-b^-`]', c in '^_`')
            if not (NORMSEP and c == '/'):
                check(c, '[d-b[-^]', c in r'[\]^')