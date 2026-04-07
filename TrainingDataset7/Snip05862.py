def search_form_tag(parser, token):
    return InclusionAdminNode(
        "search_form",
        parser,
        token,
        func=search_form,
        template_name="search_form.html",
        takes_context=False,
    )