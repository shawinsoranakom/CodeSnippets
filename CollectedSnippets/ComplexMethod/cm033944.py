def get_vars(self, loader, path, entities, cache=True):
        """ parses the inventory file """

        if not isinstance(entities, list):
            entities = [entities]

        # realpath is expensive
        try:
            realpath_basedir = CANONICAL_PATHS[path]
        except KeyError:
            CANONICAL_PATHS[path] = realpath_basedir = os.path.realpath(basedir(path))

        data = {}
        for entity in entities:
            try:
                entity_name = entity.name
            except AttributeError:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            try:
                first_char = entity_name[0]
            except (TypeError, IndexError, KeyError):
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            # avoid 'chroot' type inventory hostnames /path/to/chroot
            if first_char != os.path.sep:
                try:
                    found_files = []
                    # load vars
                    try:
                        entity_type = entity.base_type
                    except AttributeError:
                        raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

                    if entity_type is InventoryObjectType.HOST:
                        subdir = 'host_vars'
                    elif entity_type is InventoryObjectType.GROUP:
                        subdir = 'group_vars'
                    else:
                        raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

                    opath = os.path.join(realpath_basedir, subdir)
                    key = '%s.%s' % (entity_name, opath)

                    if cache:
                        if opath in NAK:
                            continue
                        if key in FOUND:
                            data = self.load_found_files(loader, data, FOUND[key])
                            continue
                    if os.path.isdir(opath):
                        self._display.debug("\tprocessing dir %s" % opath)
                        FOUND[key] = found_files = loader.find_vars_files(opath, entity_name)
                    elif not os.path.exists(opath):
                        # cache missing dirs so we don't have to keep looking for things beneath the
                        NAK.add(opath)
                    else:
                        self._display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))
                        # cache non-directory matches
                        NAK.add(opath)

                    data = self.load_found_files(loader, data, found_files)

                except Exception as e:
                    raise AnsibleParserError(to_native(e))
        return data