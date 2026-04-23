def test_fqcr_parsing_valid(ref, ref_type, expected_collection,
                            expected_subdirs, expected_resource, expected_python_pkg_name):
    assert AnsibleCollectionRef.is_valid_fqcr(ref, ref_type)

    r = AnsibleCollectionRef.from_fqcr(ref, ref_type)
    assert r.collection == expected_collection
    assert r.subdirs == expected_subdirs
    assert r.resource == expected_resource
    assert r.n_python_package_name == expected_python_pkg_name

    r = AnsibleCollectionRef.try_parse_fqcr(ref, ref_type)
    assert r.collection == expected_collection
    assert r.subdirs == expected_subdirs
    assert r.resource == expected_resource
    assert r.n_python_package_name == expected_python_pkg_name