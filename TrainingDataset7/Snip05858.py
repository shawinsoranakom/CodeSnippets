def result_list_tag(parser, token):
    return InclusionAdminNode(
        "result_list",
        parser,
        token,
        func=result_list,
        template_name="change_list_results.html",
        takes_context=False,
    )