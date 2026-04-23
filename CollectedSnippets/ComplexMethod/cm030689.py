def test_char_set(self):
        check = self.check_match
        tescases = string.ascii_lowercase + string.digits + string.punctuation
        for c in tescases:
            check(c, '[az]', c in 'az')
            check(c, '[!az]', c not in 'az')
        # Case insensitive.
        for c in tescases:
            check(c, '[AZ]', (c in 'az') and IGNORECASE)
            check(c, '[!AZ]', (c not in 'az') or not IGNORECASE)
        for c in string.ascii_uppercase:
            check(c, '[az]', (c in 'AZ') and IGNORECASE)
            check(c, '[!az]', (c not in 'AZ') or not IGNORECASE)
        # Repeated same character.
        for c in tescases:
            check(c, '[aa]', c == 'a')
        # Special cases.
        for c in tescases:
            check(c, '[^az]', c in '^az')
            check(c, '[[az]', c in '[az')
            check(c, r'[!]]', c != ']')
        check('[', '[')
        check('[]', '[]')
        check('[!', '[!')
        check('[!]', '[!]')