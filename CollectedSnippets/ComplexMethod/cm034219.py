def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        roles_path = context.CLIARGS['roles_path']

        data = ''
        for role in context.CLIARGS['args']:

            role_info = {'path': roles_path}
            gr = GalaxyRole(self.galaxy, self.lazy_role_api, role)

            install_info = gr.install_info
            if install_info:
                if 'version' in install_info:
                    install_info['installed_version'] = install_info['version']
                    del install_info['version']
                role_info.update(install_info)

            if not context.CLIARGS['offline']:
                remote_data = None
                try:
                    remote_data = self.api.lookup_role_by_name(role, False)
                except GalaxyError as e:
                    if e.http_code == 400 and 'Bad Request' in e.message:
                        # Role does not exist in Ansible Galaxy
                        data = u"- the role %s was not found" % role
                        break

                    raise AnsibleError("Unable to find info about '%s': %s" % (role, e))

                if remote_data:
                    role_info.update(remote_data)
                else:
                    data = u"- the role %s was not found" % role
                    break

            elif context.CLIARGS['offline'] and not gr._exists:
                data = u"- the role %s was not found" % role
                break

            if gr.metadata:
                role_info.update(gr.metadata)

            req = RoleRequirement()
            role_spec = req.role_yaml_parse({'role': role})
            if role_spec:
                role_info.update(role_spec)

            data += self._display_role_info(role_info)

        self.pager(data)