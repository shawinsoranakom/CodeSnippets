def change_list_object_tools_tag(parser, token):
    """Display the row of change list object tools."""
    return InclusionAdminNode(
        "change_list_object_tools",
        parser,
        token,
        func=lambda context: context,
        template_name="change_list_object_tools.html",
    )