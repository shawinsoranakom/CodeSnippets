def test_lazy_copies(value: list | dict, deep: bool, template_context: TemplateContext) -> None:
    """Verify that `copy.copy` and `copy.deepcopy` make lazy copies of lazy containers."""
    # pylint: disable=unnecessary-dunder-call
    original = _AnsibleLazyTemplateMixin._try_create(value)
    base_type = type(value)
    pseudo_lazy = base_type is tuple  # tuples do not wrap their values in `_LazyValue`

    keys: list

    if base_type is list or base_type is tuple:
        keys = list(range(len(original)))
    else:
        keys = list(original)

    assert all(isinstance(base_type.__getitem__(original, key), _LazyValue) != pseudo_lazy for key in keys)  # lazy before copy

    if deep:
        copied = copy.deepcopy(original)
    else:
        copied = copy.copy(original)

    assert copied is not original
    assert len(copied) == len(original)
    assert pseudo_lazy or all(isinstance(base_type.__getitem__(original, key), _LazyValue) != pseudo_lazy for key in keys)  # still lazy after copy

    assert all((base_type.__getitem__(copied, key) is base_type.__getitem__(original, key)) != deep for key in keys)
    assert (copied._templar is original._templar) != deep
    assert (copied._lazy_options is original._lazy_options) != deep