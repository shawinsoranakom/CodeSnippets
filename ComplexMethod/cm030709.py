def run_name_tests(self, testdata):
        names_ref = {}

        def parse_cp(s):
            return int(s, 16)

        # Parse data
        for line in testdata:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw_cp, name = line.split("; ")
            # Check for a range
            if ".." in raw_cp:
                cp1, cp2 = map(parse_cp, raw_cp.split(".."))
                # remove ‘*’ at the end
                assert name[-1] == '*', (raw_cp, name)
                name = name[:-1]
                for cp in range(cp1, cp2 + 1):
                    names_ref[cp] = f"{name}{cp:04X}"
            elif name[-1] == '*':
                cp = parse_cp(raw_cp)
                name = name[:-1]
                names_ref[cp] = f"{name}{cp:04X}"
            else:
                assert '*' not in name, (raw_cp, name)
                cp = parse_cp(raw_cp)
                names_ref[cp] = name

        for cp in range(0, sys.maxunicode + 1):
            self.assertEqual(self.db.name(chr(cp), None), names_ref.get(cp))