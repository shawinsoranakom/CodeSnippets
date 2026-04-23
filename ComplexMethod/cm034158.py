def preprocess_data(self, ds):
        """
        tasks are especially complex arguments so need pre-processing.
        keep it short.
        """

        if not isinstance(ds, dict):
            raise AnsibleAssertionError('ds (%s) should be a dict but was a %s' % (ds, type(ds)))

        # the new, cleaned datastructure, which will have legacy items reduced to a standard structure suitable for the
        # attributes of the task class; copy any tagged data to preserve things like origin
        new_ds = AnsibleTagHelper.tag_copy(ds, {})

        # since this affects the task action parsing, we have to resolve in preprocess instead of in typical validator
        default_collection = AnsibleCollectionConfig.default_collection

        collections_list = ds.get('collections')
        if collections_list is None:
            # use the parent value if our ds doesn't define it
            collections_list = self.collections
        else:
            # Validate this untemplated field early on to guarantee we are dealing with a list.
            # This is also done in CollectionSearch._load_collections() but this runs before that call.
            collections_list = self.get_validated_value('collections', self.fattributes.get('collections'), collections_list, None)

        if default_collection and not self._role:  # FIXME: and not a collections role
            if collections_list:
                if default_collection not in collections_list:
                    collections_list.insert(0, default_collection)
            else:
                collections_list = [default_collection]

        if collections_list and 'ansible.builtin' not in collections_list and 'ansible.legacy' not in collections_list:
            collections_list.append('ansible.legacy')

        if collections_list:
            ds['collections'] = collections_list

        # use the args parsing class to determine the action, args,
        # and the delegate_to value from the various possible forms
        # supported as legacy
        args_parser = ModuleArgsParser(task_ds=ds, collection_list=collections_list)
        try:
            (action, args, delegate_to) = args_parser.parse()
        except AnsibleParserError as ex:
            # if the raises exception was created with obj=ds args, then it includes the detail
            # so we dont need to add it so we can just re raise.
            if ex.obj:
                raise
            # But if it wasn't, we can add the yaml object now to get more detail
            raise AnsibleParserError("Error parsing task arguments.", obj=ds) from ex

        if args_parser._resolved_action is not None:
            self._resolved_action = args_parser._resolved_action

        new_ds['action'] = action
        new_ds['args'] = args
        new_ds['delegate_to'] = delegate_to

        # we handle any 'vars' specified in the ds here, as we may
        # be adding things to them below (special handling for includes).
        # When that deprecated feature is removed, this can be too.
        if 'vars' in ds:
            # _load_vars is defined in Base, and is used to load a dictionary
            # or list of dictionaries in a standard way
            new_ds['vars'] = self._load_vars(None, ds.get('vars'))
        else:
            new_ds['vars'] = dict()

        for (k, v) in ds.items():
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action or k == 'shell':
                # we don't want to re-assign these values, which were determined by the ModuleArgsParser() above
                continue
            elif k.startswith('with_') and k.removeprefix("with_") in lookup_loader:
                # transform into loop property
                self._preprocess_with_loop(ds, new_ds, k, v)
            elif C.INVALID_TASK_ATTRIBUTE_FAILED or k in self.fattributes:
                new_ds[k] = v
            else:
                display.warning("Ignoring invalid attribute: %s" % k)

        return super(Task, self).preprocess_data(new_ds)