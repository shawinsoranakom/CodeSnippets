def _role(name, rawtext, text, lineno, inliner, options=None, content=None):
        if options is None:
            options = {}
        _, title, target = split_explicit_title(text)
        node = docutils.nodes.reference(
            rawtext,
            title,
            refuri=(
                urlbase
                % (
                    inliner.document.settings.link_base,
                    target if is_case_sensitive else target.lower(),
                )
            ),
            **options,
        )
        return [node], []