def update_list(self):
        res = [0, 0]    # [update, add]

        default_version = modules.adapt_version('1.0')
        known_mods = self.with_context(lang=None).search([])
        known_mods_names = {mod.name: mod for mod in known_mods}

        # iterate through detected modules and update/create them in db
        for manifest in modules.Manifest.all_addon_manifests():
            mod = known_mods_names.get(manifest.name)
            terp = self.get_module_info(manifest)
            values = self.get_values_from_terp(terp)

            if mod:
                updated_values = {}
                for key in values:
                    old = getattr(mod, key)
                    if (old or values[key]) and values[key] != old:
                        updated_values[key] = values[key]
                if terp.get('installable', True) and mod.state == 'uninstallable':
                    updated_values['state'] = 'uninstalled'
                if parse_version(terp.get('version', default_version)) > parse_version(mod.latest_version or default_version):
                    res[0] += 1
                if updated_values:
                    mod.write(updated_values)
            elif not manifest or not terp:
                continue
            else:
                state = "uninstalled" if terp.get('installable', True) else "uninstallable"
                mod = self.create(dict(name=manifest.name, state=state, **values))
                res[1] += 1

            mod._update_from_terp(terp)

        return res