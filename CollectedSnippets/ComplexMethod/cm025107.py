def test_render_info_initialization(template_obj: template.Template) -> None:
    """Test RenderInfo initialization."""
    info = RenderInfo(template_obj)

    assert info.template is template_obj
    assert info._result is None
    assert info.is_static is False
    assert info.exception is None
    assert info.all_states is False
    assert info.all_states_lifecycle is False
    assert info.domains == set()
    assert info.domains_lifecycle == set()
    assert info.entities == set()
    assert info.rate_limit is None
    assert info.has_time is False
    assert info.filter_lifecycle is _true
    assert info.filter is _true