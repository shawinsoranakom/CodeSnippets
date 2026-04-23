def _get_collection_playbook_path(playbook):

    acr = AnsibleCollectionRef.try_parse_fqcr(playbook, u'playbook')
    if acr:
        try:
            # get_collection_path
            pkg = import_module(acr.n_python_collection_package_name)
        except (OSError, ModuleNotFoundError) as ex:
            # leaving ex as debug target, even though not used in normal code
            pkg = None

        if pkg:
            cpath = os.path.join(sys.modules[acr.n_python_collection_package_name].__file__.replace('__synthetic__', 'playbooks'))

            if acr.subdirs:
                paths = [_to_text(x) for x in acr.subdirs.split(u'.')]
                paths.insert(0, cpath)
                cpath = os.path.join(*paths)

            path = os.path.join(cpath, _to_text(acr.resource))
            if os.path.exists(_to_bytes(path)):
                return acr.resource, path, acr.collection
            elif not acr.resource.endswith(PB_EXTENSIONS):
                for ext in PB_EXTENSIONS:
                    path = os.path.join(cpath, _to_text(acr.resource + ext))
                    if os.path.exists(_to_bytes(path)):
                        return acr.resource, path, acr.collection
    return None