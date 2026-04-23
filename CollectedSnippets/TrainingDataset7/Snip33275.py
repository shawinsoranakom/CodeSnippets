def setup(templates, *args, **kwargs):
    blocktranslate_setup = base_setup(templates, *args, **kwargs)
    blocktrans_setup = base_setup(
        {
            name: template.replace("{% blocktranslate ", "{% blocktrans ").replace(
                "{% endblocktranslate %}", "{% endblocktrans %}"
            )
            for name, template in templates.items()
        }
    )

    tags = {
        "blocktrans": blocktrans_setup,
        "blocktranslate": blocktranslate_setup,
    }

    def decorator(func):
        @wraps(func)
        def inner(self, *args):
            signature = inspect.signature(func)
            for tag_name, setup_func in tags.items():
                if "tag_name" in signature.parameters:
                    setup_func(partial(func, tag_name=tag_name))(self)
                else:
                    setup_func(func)(self)

        return inner

    return decorator