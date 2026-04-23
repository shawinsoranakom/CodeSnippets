def test_paginator(self):
        tests = self.get_test_cases_for_test_paginator()
        for params, output in tests:
            self.check_paginator(params, output)