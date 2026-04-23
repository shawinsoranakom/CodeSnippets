def _parse_spec_group_file(base, module_base, names, update_only, with_modules):
    """Parse the names list into package specs, group specs, module specs, and filenames."""
    pkg_specs, grp_specs, module_specs, filenames = [], [], [], []
    already_loaded_comps = False

    for name in names:
        if '://' in name:
            filenames.append(name)
        elif name.endswith('.rpm'):
            filenames.append(name)
        elif name.startswith('/'):
            installed = base.sack.query().filter(provides=name, file=name).installed().run()
            if installed:
                pkg_specs.append(installed[0].name)
            elif not update_only:
                pkg_specs.append(name)
        elif name.startswith('@') or ('/' in name):
            if not already_loaded_comps:
                base.read_comps()
                already_loaded_comps = True

            grp_env_mdl_candidate = name[1:].strip()

            if with_modules and module_base:
                mdl_info = _get_modules(module_base, grp_env_mdl_candidate)
                if mdl_info['module_list'] and mdl_info['module_list'][0]:
                    module_specs.append(grp_env_mdl_candidate)
                else:
                    grp_specs.append(grp_env_mdl_candidate)
            else:
                grp_specs.append(grp_env_mdl_candidate)
        else:
            pkg_specs.append(name)

    return pkg_specs, grp_specs, module_specs, filenames