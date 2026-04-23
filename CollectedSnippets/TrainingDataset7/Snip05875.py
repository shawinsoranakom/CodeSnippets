def change_form_object_tools_tag(parser, token):
    """Display the row of change form object tools."""
    return InclusionAdminNode(
        "change_form_object_tools",
        parser,
        token,
        func=lambda context: context,
        template_name="change_form_object_tools.html",
    )