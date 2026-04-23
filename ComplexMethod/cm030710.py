def run_normalization_tests(self, testdata, ucd):
        part = None
        part1_data = set()

        NFC = partial(ucd.normalize, "NFC")
        NFKC = partial(ucd.normalize, "NFKC")
        NFD = partial(ucd.normalize, "NFD")
        NFKD = partial(ucd.normalize, "NFKD")
        is_normalized = ucd.is_normalized

        for line in testdata:
            if '#' in line:
                line = line.split('#')[0]
            line = line.strip()
            if not line:
                continue
            if line.startswith("@Part"):
                part = line.split()[0]
                continue
            c1,c2,c3,c4,c5 = [self.unistr(x) for x in line.split(';')[:-1]]

            # Perform tests
            self.assertTrue(c2 ==  NFC(c1) ==  NFC(c2) ==  NFC(c3), line)
            self.assertTrue(c4 ==  NFC(c4) ==  NFC(c5), line)
            self.assertTrue(c3 ==  NFD(c1) ==  NFD(c2) ==  NFD(c3), line)
            self.assertTrue(c5 ==  NFD(c4) ==  NFD(c5), line)
            self.assertTrue(c4 == NFKC(c1) == NFKC(c2) == \
                            NFKC(c3) == NFKC(c4) == NFKC(c5),
                            line)
            self.assertTrue(c5 == NFKD(c1) == NFKD(c2) == \
                            NFKD(c3) == NFKD(c4) == NFKD(c5),
                            line)

            self.assertTrue(is_normalized("NFC", c2))
            self.assertTrue(is_normalized("NFC", c4))

            self.assertTrue(is_normalized("NFD", c3))
            self.assertTrue(is_normalized("NFD", c5))

            self.assertTrue(is_normalized("NFKC", c4))
            self.assertTrue(is_normalized("NFKD", c5))

            # Record part 1 data
            if part == "@Part1":
                part1_data.add(c1)

        # Perform tests for all other data
        for X in iterallchars():
            if X in part1_data:
                continue
            self.assertTrue(X == NFC(X) == NFD(X) == NFKC(X) == NFKD(X), ord(X))