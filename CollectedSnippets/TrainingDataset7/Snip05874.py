def submit_row_tag(parser, token):
    return InclusionAdminNode(
        "submit_row", parser, token, func=submit_row, template_name="submit_line.html"
    )