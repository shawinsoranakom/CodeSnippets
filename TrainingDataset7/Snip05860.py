def date_hierarchy_tag(parser, token):
    return InclusionAdminNode(
        "date_hierarchy",
        parser,
        token,
        func=date_hierarchy,
        template_name="date_hierarchy.html",
        takes_context=False,
    )