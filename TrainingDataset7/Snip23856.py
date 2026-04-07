def get_paginator(
        self, queryset, page_size, orphans=0, allow_empty_first_page=True
    ):
        return super().get_paginator(
            queryset,
            page_size,
            orphans=2,
            allow_empty_first_page=allow_empty_first_page,
        )