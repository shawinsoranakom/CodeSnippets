async def check_paginator_async(self, params, output):
        """See check_paginator."""
        count, num_pages, page_range = output
        paginator = AsyncPaginator(*params)
        await self.check_attribute_async("acount", paginator, count, params)
        await self.check_attribute_async("anum_pages", paginator, num_pages, params)