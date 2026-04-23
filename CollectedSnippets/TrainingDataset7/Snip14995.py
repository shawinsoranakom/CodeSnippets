def html_page_context_hook(app, pagename, templatename, context, doctree):
    # Put a bool on the context used to render the template. It's used to
    # control inclusion of console-tabs.css and activation of the JavaScript.
    # This way it's include only from HTML files rendered from reST files where
    # the ConsoleDirective is used.
    context["include_console_assets"] = getattr(
        doctree, "_console_directive_used_flag", False
    )