def run(self, terms: list, variables=None, **kwargs):
        if (first_marker := _template.get_first_marker_arg((), kwargs)) is not None:
            first_marker.trip()

        # if we're being invoked by TaskExecutor.get_loop_items(),
        # recursively drop undefined values from terms for backwards compatibility
        terms = _recurse_terms(terms, omit_undefined=_jinja_plugins._LookupContext.current().invoked_as_with)

        try:
            # invoked_as_with shouldn't be possible outside a TaskContext
            te_action = _task.TaskContext.current().task.action  # FIXME: this value has not been templated, it should be (historical problem)...
        except ReferenceError:
            te_action = 'file'

        # based on the presence of `var`/`template`/`file` in the enclosing task action name, choose a subdir to search
        for subdir in ['template', 'var', 'file']:
            if subdir in te_action:
                break

        subdir += "s"  # convert to the matching directory name
        self.set_options(var_options=variables, direct=kwargs)

        if not terms:
            terms = self.get_option('files')

        total_search = self._process_terms(terms, variables)

        # NOTE: during refactor noticed that the 'using a dict' as term
        # is designed to only work with 'one' otherwise inconsistencies will appear.
        # see other notes below.

        for fn in total_search:
            # get subdir if set by task executor, default to files otherwise
            path = self.find_file_in_search_path(variables, subdir, fn, ignore_missing=True)

            # exit if we find one!
            if path is not None:
                return [unfrackpath(path, follow=False)]

        skip = self.get_option('skip')

        # if we get here, no file was found
        if skip:
            # NOTE: global skip won't matter, only last 'skip' value in dict term
            return []

        raise AnsibleError("No file was found when using first_found.")