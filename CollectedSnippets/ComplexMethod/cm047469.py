def migrate_module(self, pkg: module_graph.ModuleNode, stage: typing.Literal['pre', 'post', 'end']) -> None:
        assert stage in ('pre', 'post', 'end')
        stageformat = {
            'pre': '[>%s]',
            'post': '[%s>]',
            'end': '[$%s]',
        }
        if pkg.load_state != 'to upgrade' and pkg.name not in Registry(self.cr.dbname)._force_upgrade_scripts:
            return

        def convert_version(version: str) -> str:
            if version == "0.0.0":
                return version
            if version.count(".") > 2:
                return version  # the version number already contains the server version, see VERSION_RE for details
            return "%s.%s" % (release.major_version, version)

        def _get_migration_versions(pkg, stage: str) -> list[str]:
            versions = sorted({
                ver: None
                for lv in self.migrations[pkg.name].values()
                for ver, lf in lv.items()
                if lf
            }, key=lambda k: parse_version(convert_version(k)))
            if "0.0.0" in versions:
                # reorder versions
                versions.remove("0.0.0")
                if stage == "pre":
                    versions.insert(0, "0.0.0")
                else:
                    versions.append("0.0.0")
            return versions

        def _get_migration_files(pkg, version, stage):
            """ return a list of migration script files
            """
            m = self.migrations[pkg.name]

            return sorted(
                (
                    f
                    for k in m
                    for f in m[k].get(version, [])
                    if os.path.basename(f).startswith(f"{stage}-")
                ),
                key=os.path.basename,
            )

        installed_version = pkg.load_version or ''
        parsed_installed_version = parse_version(installed_version)
        current_version = parse_version(convert_version(pkg.manifest['version']))

        def compare(version: str) -> bool:
            if version == "0.0.0" and parsed_installed_version < current_version:
                return True

            full_version = convert_version(version)
            majorless_version = (version != full_version)

            if majorless_version:
                # We should not re-execute major-less scripts when upgrading to new Odoo version
                # a module in `9.0.2.0` should not re-execute a `2.0` script when upgrading to `10.0.2.0`.
                # In which case we must compare just the module version
                return parsed_installed_version[2:] < parse_version(full_version)[2:] <= current_version[2:]

            return parsed_installed_version < parse_version(full_version) <= current_version

        versions = _get_migration_versions(pkg, stage)
        for version in versions:
            if compare(version):
                for pyfile in _get_migration_files(pkg, version, stage):
                    exec_script(self.cr, installed_version, pyfile, pkg.name, stage, stageformat[stage] % version)