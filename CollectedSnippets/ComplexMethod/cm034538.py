def _get_collection_resource_path(name, ref_type, collection_list=None):

    if ref_type == u'playbook':
        # they are handled a bit diff due to 'extension variance' and no collection_list
        return _get_collection_playbook_path(name)

    acr = AnsibleCollectionRef.try_parse_fqcr(name, ref_type)
    if acr:
        # looks like a valid qualified collection ref; skip the collection_list
        collection_list = [acr.collection]
        subdirs = acr.subdirs
        resource = acr.resource
    elif not collection_list:
        return None  # not a FQ and no collection search list spec'd, nothing to do
    else:
        resource = name  # treat as unqualified, loop through the collection search list to try and resolve
        subdirs = ''

    for collection_name in collection_list:
        try:
            acr = AnsibleCollectionRef(collection_name=collection_name, subdirs=subdirs, resource=resource, ref_type=ref_type)
            # FIXME: error handling/logging; need to catch any import failures and move along
            pkg = import_module(acr.n_python_package_name)

            if pkg is not None:
                # the package is now loaded, get the collection's package and ask where it lives
                path = os.path.dirname(_to_bytes(sys.modules[acr.n_python_package_name].__file__))
                return resource, _to_text(path), collection_name

        except (OSError, ModuleNotFoundError) as ex:
            continue
        except Exception as ex:
            # FIXME: pick out typical import errors first, then error logging
            continue

    return None