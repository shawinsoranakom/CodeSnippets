def test_collectionref_components_valid(name, subdirs, resource, ref_type, python_pkg_name):
    x = AnsibleCollectionRef(name, subdirs, resource, ref_type)

    assert x.collection == name
    if subdirs:
        assert x.subdirs == subdirs
    else:
        assert x.subdirs == ''

    assert x.resource == resource
    assert x.ref_type == ref_type
    assert x.n_python_package_name == python_pkg_name