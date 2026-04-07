def store_rendered_templates(store, signal, sender, template, context, **kwargs):
    """
    Store templates and contexts that are rendered.

    The context is copied so that it is an accurate representation at the time
    of rendering.
    """
    store.setdefault("templates", []).append(template)
    if "context" not in store:
        store["context"] = ContextList()
    store["context"].append(copy(context))