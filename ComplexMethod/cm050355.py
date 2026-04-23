def _get_missing_dependencies_modules(self, zip_data):
        dependencies_to_install = self.env['ir.module.module']
        known_mods = self.search([('to_buy', '=', False)])
        installed_mods = [m.name for m in known_mods if m.state == 'installed']
        not_found_modules = set()
        with zipfile.ZipFile(BytesIO(zip_data), "r") as z:
            manifest_files = [
                file
                for file in z.infolist()
                if file.filename.count('/') == 1
                and file.filename.split('/')[1] in MANIFEST_NAMES
            ]
            modules_in_zip = {manifest.filename.split('/')[0] for manifest in manifest_files}
            for manifest_file in manifest_files:
                if manifest_file.file_size > MAX_FILE_SIZE:
                    raise UserError(_("File '%s' exceed maximum allowed file size", manifest_file.filename))
                try:
                    with z.open(manifest_file) as manifest:
                        terp = ast.literal_eval(manifest.read().decode())
                except Exception:
                    continue
                unmet_dependencies = set(terp.get('depends', [])).difference(installed_mods, modules_in_zip)
                dependencies_to_install |= known_mods.filtered(lambda m: m.name in unmet_dependencies)
                not_found_modules |= set(
                    mod for mod in unmet_dependencies if mod not in dependencies_to_install.mapped('name')
                )
        return dependencies_to_install, not_found_modules