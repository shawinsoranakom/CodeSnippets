def admin_list_filter(cl, spec):
    tpl = get_template(spec.template)
    return tpl.render(
        {
            "title": spec.title,
            "choices": list(spec.choices(cl)),
            "spec": spec,
        }
    )