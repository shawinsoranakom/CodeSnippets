def get_paginator(
        self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    ):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)