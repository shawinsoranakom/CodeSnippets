def select_template(template_name_list, using=None):
    """
    Load and return a template for one of the given names.

    Try names in order and return the first template found.

    Raise TemplateDoesNotExist if no such template exists.
    """
    if isinstance(template_name_list, str):
        raise TypeError(
            "select_template() takes an iterable of template names but got a "
            "string: %r. Use get_template() if you want to load a single "
            "template by name." % template_name_list
        )

    chain = []
    engines = _engine_list(using)
    for template_name in template_name_list:
        for engine in engines:
            try:
                return engine.get_template(template_name)
            except TemplateDoesNotExist as e:
                chain.append(e)

    if template_name_list:
        raise TemplateDoesNotExist(", ".join(template_name_list), chain=chain)
    else:
        raise TemplateDoesNotExist("No template names provided")