def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="templatetag",
        rolename="ttag",
        indextemplate="pair: %s; template tag",
    )
    app.add_crossref_type(
        directivename="templatefilter",
        rolename="tfilter",
        indextemplate="pair: %s; template filter",
    )
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )
    app.add_object_type(
        directivename="django-admin",
        rolename="djadmin",
        indextemplate="pair: %s; django-admin command",
        parse_node=parse_django_admin_node,
    )
    app.add_directive("django-admin-option", Cmdoption)
    app.add_config_value("django_next_version", "0.0", True)
    app.add_directive("versionadded", VersionDirective)
    app.add_directive("versionchanged", VersionDirective)
    app.add_builder(DjangoStandaloneHTMLBuilder)
    app.set_translator("djangohtml", DjangoHTMLTranslator)
    app.set_translator("json", DjangoHTMLTranslator)
    app.add_node(
        ConsoleNode,
        html=(visit_console_html, None),
        latex=(visit_console_dummy, depart_console_dummy),
        man=(visit_console_dummy, depart_console_dummy),
        text=(visit_console_dummy, depart_console_dummy),
        texinfo=(visit_console_dummy, depart_console_dummy),
    )
    app.add_directive("console", ConsoleDirective)
    app.connect("html-page-context", html_page_context_hook)
    app.add_role("default-role-error", default_role_error)
    return {"parallel_read_safe": True}