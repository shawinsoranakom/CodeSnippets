def execute_install(self, artifacts_manager=None):
        """
        Install one or more roles(``ansible-galaxy role install``), or one or more collections(``ansible-galaxy collection install``).
        You can pass in a list (roles or collections) or use the file
        option listed below (these are mutually exclusive). If you pass in a list, it
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local tar archive file.
        """
        install_items = context.CLIARGS['args']
        requirements_file = context.CLIARGS['requirements']
        collection_path = None
        signatures = context.CLIARGS.get('signatures')
        if signatures is not None:
            signatures = list(signatures)

        if requirements_file:
            requirements_file = GalaxyCLI._resolve_path(requirements_file)

        two_type_warning = "The requirements file '%s' contains {0}s which will be ignored. To install these {0}s " \
                           "run 'ansible-galaxy {0} install -r' or to install both at the same time run " \
                           "'ansible-galaxy install -r' without a custom install path." % to_text(requirements_file)

        # TODO: Would be nice to share the same behaviour with args and -r in collections and roles.
        collection_requirements = []
        role_requirements = []
        if context.CLIARGS['type'] == 'collection':
            collection_path = GalaxyCLI._resolve_path(context.CLIARGS['collections_path'])
            requirements = self._require_one_of_collections_requirements(
                install_items, requirements_file,
                signatures=signatures,
                artifacts_manager=artifacts_manager,
            )

            collection_requirements = requirements['collections']
            if requirements['roles']:
                display.vvv(two_type_warning.format('role'))
        else:
            if not install_items and requirements_file is None:
                raise AnsibleOptionsError("- you must specify a user/role name or a roles file")

            if requirements_file:
                if not (requirements_file.endswith('.yaml') or requirements_file.endswith('.yml')):
                    raise AnsibleError("Invalid role requirements file, it must end with a .yml or .yaml extension")

                galaxy_args = self._raw_args
                will_install_collections = self._implicit_role and '-p' not in galaxy_args and '--roles-path' not in galaxy_args

                requirements = self._parse_requirements_file(
                    requirements_file,
                    artifacts_manager=artifacts_manager,
                    validate_signature_options=will_install_collections,
                )
                role_requirements = requirements['roles']

                # We can only install collections and roles at the same time if the type wasn't specified and the -p
                # argument was not used. If collections are present in the requirements then at least display a msg.
                if requirements['collections'] and (not self._implicit_role or '-p' in galaxy_args or
                                                    '--roles-path' in galaxy_args):

                    # We only want to display a warning if 'ansible-galaxy install -r ... -p ...'. Other cases the user
                    # was explicit about the type and shouldn't care that collections were skipped.
                    display_func = display.warning if self._implicit_role else display.vvv
                    display_func(two_type_warning.format('collection'))
                else:
                    collection_path = self._get_default_collection_path()
                    collection_requirements = requirements['collections']
            else:
                # roles were specified directly, so we'll just go out grab them
                # (and their dependencies, unless the user doesn't want us to).
                for rname in context.CLIARGS['args']:
                    role = RoleRequirement.role_yaml_parse(rname.strip())
                    role_requirements.append(GalaxyRole(self.galaxy, self.lazy_role_api, **role))

        if not role_requirements and not collection_requirements:
            display.display("Skipping install, no requirements found")
            return

        if role_requirements:
            display.display("Starting galaxy role install process")
            self._execute_install_role(role_requirements)

        if collection_requirements:
            display.display("Starting galaxy collection install process")
            # Collections can technically be installed even when ansible-galaxy is in role mode so we need to pass in
            # the install path as context.CLIARGS['collections_path'] won't be set (default is calculated above).
            self._execute_install_collection(
                collection_requirements, collection_path,
                artifacts_manager=artifacts_manager,
            )