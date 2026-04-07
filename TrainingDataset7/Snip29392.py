async def test_paginator_async(self):
        tests = self.get_test_cases_for_test_paginator()
        for params, output in tests:
            await self.check_paginator_async(params, output)