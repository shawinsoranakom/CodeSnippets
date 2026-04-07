def pagination_tag(parser, token):
    return InclusionAdminNode(
        "pagination",
        parser,
        token,
        func=pagination,
        template_name="pagination.html",
        takes_context=False,
    )