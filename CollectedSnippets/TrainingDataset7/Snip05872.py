def prepopulated_fields_js_tag(parser, token):
    return InclusionAdminNode(
        "prepopulated_fields_js",
        parser,
        token,
        func=prepopulated_fields_js,
        template_name="prepopulated_fields_js.html",
    )