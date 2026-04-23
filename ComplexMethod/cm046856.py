def _has_add_generation_prompt_block(chat_template):
    """True if the template has a *positive* `{% if add_generation_prompt %}`
    gate whose body emits output. Rejects header guards like
    `{% if not add_generation_prompt is defined %}{% set ... %}{% endif %}`
    that reference the name but emit nothing. AST-based; string-scan
    fallback if Jinja fails to parse."""
    try:
        import jinja2
        import jinja2.nodes

        ast = jinja2.Environment().parse(chat_template)
    except Exception:
        return "if add_generation_prompt" in chat_template and "%}" in chat_template
    for if_node in ast.find_all(jinja2.nodes.If):
        test = if_node.test
        # Reject negated gates: `{% if not add_generation_prompt %}` fires
        # when agp=False, so it's not a generation block even if it emits.
        if isinstance(test, jinja2.nodes.Not):
            continue
        # find_all skips the test root, so check bare Name tests explicitly.
        references_agp = False
        if isinstance(test, jinja2.nodes.Name) and test.name == "add_generation_prompt":
            references_agp = True
        else:
            for name_node in test.find_all(jinja2.nodes.Name):
                if name_node.name == "add_generation_prompt":
                    references_agp = True
                    break
        if references_agp and _if_body_emits_content(if_node):
            return True
    return False