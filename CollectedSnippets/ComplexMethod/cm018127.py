def test_overrides_normalized() -> None:
    """Test override lists are using normalized package names."""
    for req in gen_requirements_all.EXCLUDED_REQUIREMENTS_ALL:
        assert req == gen_requirements_all._normalize_package_name(req)
    for req in gen_requirements_all.INCLUDED_REQUIREMENTS_WHEELS:
        assert req == gen_requirements_all._normalize_package_name(req)
    for overrides in gen_requirements_all.OVERRIDDEN_REQUIREMENTS_ACTIONS.values():
        for req in overrides["exclude"]:
            assert req == gen_requirements_all._normalize_package_name(req)
        for req in overrides["include"]:
            assert req == gen_requirements_all._normalize_package_name(req)