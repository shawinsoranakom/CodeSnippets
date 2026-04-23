def test_container_comparison(container_type: type) -> None:
    templar = TemplateEngine()

    # including default('goodbye') as canary for flattening to a string
    value = container_type([VALUE_TO_TEMPLATE])
    rendered = templar.template(value)

    with TemplateContext(template_value=None, templar=templar, options=TemplateOptions(), stop_on_template=False):
        # NOTE: Assertion failure helper text may be misleading, since repr() will show rendered templates, which will appear to match expected values.

        lazy = _AnsibleLazyTemplateMixin._try_create(value)

        assert value > rendered
        assert not (lazy > rendered)  # pylint: disable=unnecessary-negation

        assert value >= rendered
        assert lazy >= rendered

        assert rendered < value
        assert not (rendered < lazy)  # pylint: disable=unnecessary-negation

        assert rendered <= value
        assert rendered <= lazy