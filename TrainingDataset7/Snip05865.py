def admin_actions_tag(parser, token):
    return InclusionAdminNode(
        "admin_actions", parser, token, func=admin_actions, template_name="actions.html"
    )