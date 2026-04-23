def execute_list_role(self):
        """
        List all roles installed on the local system or a specific role
        """

        path_found = False
        role_found = False
        warnings = []
        roles_search_paths = context.CLIARGS['roles_path']
        role_name = context.CLIARGS['role']

        for path in roles_search_paths:
            role_path = GalaxyCLI._resolve_path(path)
            if os.path.isdir(path):
                path_found = True
            else:
                warnings.append("- the configured path {0} does not exist.".format(path))
                continue

            if role_name:
                # show the requested role, if it exists
                gr = GalaxyRole(self.galaxy, self.lazy_role_api, role_name, path=os.path.join(role_path, role_name))
                if os.path.isdir(gr.path):
                    role_found = True
                    display.display('# %s' % os.path.dirname(gr.path))
                    _display_role(gr)
                    break
                warnings.append("- the role %s was not found" % role_name)
            else:
                if not os.path.exists(role_path):
                    warnings.append("- the configured path %s does not exist." % role_path)
                    continue

                if not os.path.isdir(role_path):
                    warnings.append("- the configured path %s, exists, but it is not a directory." % role_path)
                    continue

                display.display('# %s' % role_path)
                path_files = os.listdir(role_path)
                for path_file in path_files:
                    gr = GalaxyRole(self.galaxy, self.lazy_role_api, path_file, path=path)
                    if gr.metadata:
                        _display_role(gr)

        # Do not warn if the role was found in any of the search paths
        if role_found and role_name:
            warnings = []

        for w in warnings:
            display.warning(w)

        if not path_found:
            display.warning(
                "None of the provided paths were usable. Please specify a valid path with --{0}s-path.".format(context.CLIARGS['type'])
            )

        return 0