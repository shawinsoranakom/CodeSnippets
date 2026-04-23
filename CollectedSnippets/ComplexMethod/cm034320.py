def _finalize_template_result(o: t.Any, mode: FinalizeMode) -> t.Any:
    """Recurse the template result, rendering any encountered templates, converting containers to non-lazy versions."""
    # DTFIX5: add tests to ensure this method doesn't drift from allowed types
    o_type = type(o)

    # DTFIX-FUTURE: provide an optional way to check for trusted templates leaking out of templating (injected, but not passed through templar.template)

    if o_type is _AnsibleTaggedStr:
        return _JinjaConstTemplate.untag(o)  # prevent _JinjaConstTemplate from leaking into finalized results

    if o_type in PASS_THROUGH_SCALAR_VAR_TYPES:
        return o

    if o_type in _FINALIZE_FAST_PATH_EXACT_MAPPING_TYPES:  # silently convert known mapping types to dict
        return _finalize_collection(o, mode, _finalize_dict, dict)

    if o_type in _FINALIZE_FAST_PATH_EXACT_ITERABLE_TYPES:  # silently convert known sequence types to list
        return _finalize_collection(o, mode, _finalize_list, list)

    if o_type in Marker._concrete_subclasses:  # this early return assumes handle_marker follows our variable type rules
        return TemplateContext.current().templar.marker_behavior.handle_marker(o)

    if mode is not FinalizeMode.TOP_LEVEL:  # unsupported type (do not raise)
        return o

    if o_type in _FINALIZE_DISALLOWED_EXACT_TYPES:  # early abort for disallowed types that would otherwise be handled below
        raise AnsibleVariableTypeError.from_value(obj=o)

    if _internal.is_intermediate_mapping(o):  # since isinstance checks are slower, this is separate from the exact type check above
        return _finalize_fallback_collection(o, mode, _finalize_dict, dict)

    if _internal.is_intermediate_iterable(o):  # since isinstance checks are slower, this is separate from the exact type check above
        return _finalize_fallback_collection(o, mode, _finalize_list, list)

    if (result := _maybe_finalize_scalar(o)) is not None:
        return result

    raise AnsibleVariableTypeError.from_value(obj=o)