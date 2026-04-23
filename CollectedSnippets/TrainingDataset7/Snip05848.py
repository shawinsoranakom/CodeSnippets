def paginator_number(cl, i):
    """
    Generate an individual page index link in a paginated list.
    """
    if i == cl.paginator.ELLIPSIS:
        return format_html("{} ", cl.paginator.ELLIPSIS)
    elif i == cl.page_num:
        return format_html(
            '<a role="button" href="" aria-current="page">{}</a> ',
            i,
        )
    else:
        return format_html(
            '<a role="button" href="{}">{}</a> ',
            cl.get_query_string({PAGE_VAR: i}),
            i,
        )