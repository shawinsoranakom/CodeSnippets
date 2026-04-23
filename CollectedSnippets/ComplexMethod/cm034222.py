def _execute_install_role(self, requirements):
        role_file = context.CLIARGS['requirements']
        no_deps = context.CLIARGS['no_deps']
        force_deps = context.CLIARGS['force_with_deps']
        force = context.CLIARGS['force'] or force_deps

        for role in requirements:
            # only process roles in roles files when names matches if given
            if role_file and context.CLIARGS['args'] and role.name not in context.CLIARGS['args']:
                display.vvv('Skipping role %s' % role.name)
                continue

            display.vvv('Processing role %s ' % role.name)

            # query the galaxy API for the role data

            if role.install_info is not None:
                if role.install_info['version'] != role.version or force:
                    if force:
                        display.display('- changing role %s from %s to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        role.remove()
                    else:
                        display.warning('- %s (%s) is already installed - use --force to change version to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        continue
                else:
                    if not force:
                        display.display('- %s is already installed, skipping.' % str(role))
                        continue

            try:
                installed = role.install()
            except AnsibleError as e:
                display.warning(u"- %s was NOT installed successfully: %s " % (role.name, to_text(e)))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            if not no_deps and installed:
                if not role.metadata:
                    # NOTE: the meta file is also required for installing the role, not just dependencies
                    display.warning("Meta file %s is empty. Skipping dependencies." % role.path)
                else:
                    role_dependencies = role.metadata_dependencies + role.requirements
                    for dep in role_dependencies:
                        display.debug('Installing dep %s' % dep)
                        dep_req = RoleRequirement()
                        dep_info = dep_req.role_yaml_parse(dep)
                        dep_role = GalaxyRole(self.galaxy, self.lazy_role_api, **dep_info)
                        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                            # we know we can skip this, as it's not going to
                            # be found on galaxy.ansible.com
                            continue
                        if dep_role.install_info is None:
                            if dep_role not in requirements:
                                display.display('- adding dependency: %s' % to_text(dep_role))
                                requirements.append(dep_role)
                            else:
                                display.display('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                if force_deps:
                                    display.display('- changing dependent role %s from %s to %s' %
                                                    (dep_role.name, dep_role.install_info['version'], dep_role.version or "unspecified"))
                                    dep_role.remove()
                                    requirements.append(dep_role)
                                else:
                                    display.warning('- dependency %s (%s) from role %s differs from already installed version (%s), skipping' %
                                                    (to_text(dep_role), dep_role.version, role.name, dep_role.install_info['version']))
                            else:
                                if force_deps:
                                    requirements.append(dep_role)
                                else:
                                    display.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                display.warning("- %s was NOT installed successfully." % role.name)
                self.exit_without_ignore()

        return 0