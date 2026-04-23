def test_list(self):
        data = self.run_py(["--list"])
        found = {}
        expect = {}
        for line in data["stdout"].splitlines():
            m = re.match(r"\s*(.+?)\s+?(\*\s+)?(.+)$", line)
            if m:
                found[m.group(1)] = m.group(3)
        for company in TEST_DATA:
            company_data = TEST_DATA[company]
            tags = [t for t in company_data if isinstance(company_data[t], dict)]
            for tag in tags:
                arg = f"-V:{company}/{tag}"
                expect[arg] = company_data[tag]["DisplayName"]
            expect.pop(f"-V:{company}/ignored", None)

        actual = {k: v for k, v in found.items() if k in expect}
        try:
            self.assertDictEqual(expect, actual)
        except:
            if support.verbose:
                print("*** STDOUT ***")
                print(data["stdout"])
            raise