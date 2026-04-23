def lazy_value(self, non_lazy_value, request: pytest.FixtureRequest, template_context):
        value_type = None  # DTFIX-FUTURE: get from request when needed, can't easily add to the static fixture list- the generator cases are not being tested
        if value_type:
            if isinstance(non_lazy_value, c.Mapping):
                generator = ((k, v) for k, v in non_lazy_value.items())
            else:
                generator = (item for item in non_lazy_value)

            value = generator

        else:
            value = _AnsibleLazyTemplateMixin._try_create(non_lazy_value)

        # any tests not marked `pytest.mark.allow_delazify` will supply a lazy with its _templar removed and assert that it's still empty afterward
        allow_delazify = any(request.node.iter_markers('allow_delazify'))

        if isinstance(value, _AnsibleLazyTemplateMixin) and not allow_delazify:
            assert value._templar
            # supply a non-functional, but non-None templar, forcing an error if lazy behavior is triggered during tagging
            value._templar = object()  # type: ignore[assignment]

        yield value  # yield to the test; we'll validate later

        # LazyAccessTuple can't template, so we can't induce this failure
        if isinstance(value, _AnsibleLazyTemplateMixin) and not allow_delazify and not isinstance(value, _AnsibleLazyAccessTuple):
            with pytest.raises(AttributeError):
                # verify using the templar fails by using a method which relies on it (to ensure our templar hack above worked)
                t.cast(AnsibleTaggedObject, value)._native_copy()