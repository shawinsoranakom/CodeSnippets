def check_paginator(self, params, output):
        """
        Helper method that instantiates a Paginator object from the passed
        params and then checks that its attributes match the passed output.
        """
        count, num_pages, page_range = output
        paginator = Paginator(*params)
        self.check_attribute("count", paginator, count, params)
        self.check_attribute("num_pages", paginator, num_pages, params)
        self.check_attribute("page_range", paginator, page_range, params, coerce=list)