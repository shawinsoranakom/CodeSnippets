def check_external_dependencies(self, module_name, newstate='to install'):
        manifest = modules.Manifest.for_addon(module_name)
        if not manifest:
            return  # unavailable module, there is no point in checking dependencies
        try:
            manifest.check_manifest_dependencies()
        except MissingDependency as e:
            if newstate == 'to install':
                msg = _('Unable to install module "%(module)s" because an external dependency is not met: %(dependency)s', module=module_name, dependency=e.dependency)
            elif newstate == 'to upgrade':
                msg = _('Unable to upgrade module "%(module)s" because an external dependency is not met: %(dependency)s', module=module_name, dependency=e.dependency)
            else:
                msg = _('Unable to process module "%(module)s" because an external dependency is not met: %(dependency)s', module=module_name, dependency=e.dependency)

            install_package = None
            if platform.system() == 'Linux':
                distro = platform.freedesktop_os_release()
                id_likes = {distro['ID'], *distro.get('ID_LIKE', '').split()}
                if 'debian' in id_likes or 'ubuntu' in id_likes:
                    if package := manifest['external_dependencies'].get('apt', {}).get(e.dependency):
                        install_package = f'apt install {package}'

            if install_package:
                msg += _("\nIt can be installed running: %s", install_package)

            raise UserError(msg) from e