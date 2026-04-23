def _import_module(self, module, path, force=False, with_demo=False):
        # Do not create a bridge module for these neutralizations.
        # Do not involve specific website during import by resetting
        # information used by website's get_current_website.
        self = self.with_context(website_id=None)  # noqa: PLW0642
        force_website_id = None
        if request and request.session.get('force_website_id'):
            force_website_id = request.session.pop('force_website_id')

        known_mods = self.search([])
        known_mods_names = {m.name: m for m in known_mods}
        installed_mods = [m.name for m in known_mods if m.state == 'installed']

        terp = Manifest._from_path(path, env=self.env)
        if not terp:
            return False
        values = self.get_values_from_terp(terp)
        try:
            icon_path = terp.raw_value('icon') or opj(terp.name, 'static/description/icon.png')
            file_path(icon_path, env=self.env, check_exists=True)
            values['icon'] = '/' + icon_path
        except OSError:
            pass  # keep the default icon
        values['latest_version'] = terp.version
        if self.env.context.get('data_module'):
            values['module_type'] = 'industries'
        if with_demo:
            values['demo'] = True

        unmet_dependencies = set(terp.get('depends', [])).difference(installed_mods)

        if unmet_dependencies:
            wrong_dependencies = unmet_dependencies.difference(known_mods.mapped("name"))
            if wrong_dependencies:
                err = _("Unknown module dependencies:") + "\n - " + "\n - ".join(wrong_dependencies)
                raise UserError(err)
            to_install = known_mods.filtered(lambda mod: mod.name in unmet_dependencies)
            to_install.button_immediate_install()
        elif 'web_studio' not in installed_mods and _is_studio_custom(path):
            raise UserError(_("Studio customizations require the Odoo Studio app."))

        mod = known_mods_names.get(module)
        if mod:
            mod.write(dict(state='installed', **values))
            mode = 'update' if not force else 'init'
        else:
            assert terp.get('installable', True), "Module not installable"
            mod = self.create(dict(name=module, state='installed', imported=True, **values))
            mode = 'init'

        exclude_list = set()
        base_dir = pathlib.Path(path)
        for pattern in terp.get('cloc_exclude', []):
            exclude_list.update(str(p.relative_to(base_dir)) for p in base_dir.glob(pattern) if p.is_file())

        kind_of_files = ['data', 'init_xml']
        if with_demo:
            kind_of_files.append('demo')
        for kind in kind_of_files:
            for filename in terp.get(kind, []):
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ('.xml', '.csv', '.sql'):
                    _logger.info("module %s: skip unsupported file %s", module, filename)
                    continue
                _logger.info("module %s: loading %s", module, filename)
                noupdate = ext == '.csv' and kind == 'init_xml'
                pathname = opj(path, filename)
                idref = {}
                convert_file(self.env, module, filename, idref, mode, noupdate, pathname=pathname)
                if filename in exclude_list:
                    for xml_id, rec_id in idref.items():
                        name = xml_id.replace('.', '_')
                        if self.env.ref(f"__cloc_exclude__.{name}", raise_if_not_found=False):
                            continue
                        self.env['ir.model.data'].create([{
                            'name': name,
                            'model': self.env['ir.model.data']._xmlid_lookup(xml_id)[0],
                            'module': "__cloc_exclude__",
                            'res_id': rec_id,
                        }])

        path_static = opj(path, 'static')
        IrAttachment = self.env['ir.attachment']
        if os.path.isdir(path_static):
            for root, _dirs, files in os.walk(path_static):
                for static_file in files:
                    full_path = opj(root, static_file)
                    with file_open(full_path, 'rb', env=self.env) as fp:
                        data = base64.b64encode(fp.read())
                    url_path = '/{}{}'.format(module, full_path.split(path)[1].replace(os.path.sep, '/'))
                    if not isinstance(url_path, str):
                        url_path = url_path.decode(sys.getfilesystemencoding())
                    filename = os.path.split(url_path)[1]
                    values = dict(
                        name=filename,
                        url=url_path,
                        res_model='ir.ui.view',
                        type='binary',
                        datas=data,
                    )
                    # Do not create a bridge module for this check.
                    if 'public' in IrAttachment._fields:
                        # Static data is public and not website-specific.
                        values['public'] = True
                    attachment = IrAttachment.sudo().search([('url', '=', url_path), ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')])
                    if attachment:
                        attachment.write(values)
                    else:
                        attachment = IrAttachment.create(values)
                        self.env['ir.model.data'].create({
                            'name': f"attachment_{url_path}".replace('.', '_').replace(' ', '_'),
                            'model': 'ir.attachment',
                            'module': module,
                            'res_id': attachment.id,
                        })
                        if str(pathlib.Path(full_path).relative_to(base_dir)) in exclude_list:
                            self.env['ir.model.data'].create({
                                'name': f"cloc_exclude_attachment_{url_path}".replace('.', '_').replace(' ', '_'),
                                'model': 'ir.attachment',
                                'module': "__cloc_exclude__",
                                'res_id': attachment.id,
                            })

        # store translation files as attachments to allow loading translations for webclient
        path_lang = opj(path, 'i18n')
        if os.path.isdir(path_lang):
            for entry in os.scandir(path_lang):
                if not entry.is_file() or not entry.name.endswith('.po'):
                    # we don't support sub-directories in i18n
                    continue
                with file_open(entry.path, 'rb', env=self.env) as fp:
                    raw = fp.read()
                lang = entry.name.split('.')[0]
                # store as binary ir.attachment
                values = {
                    'name': f'{module}_{lang}.po',
                    'url': f'/{module}/i18n/{lang}.po',
                    'res_model': 'ir.module.module',
                    'res_id': mod.id,
                    'type': 'binary',
                    'raw': raw,
                }
                attachment = IrAttachment.sudo().search([('url', '=', values['url']), ('type', '=', 'binary'), ('name', '=', values['name'])])
                if attachment:
                    attachment.write(values)
                else:
                    attachment = IrAttachment.create(values)
                    self.env['ir.model.data'].create({
                        'name': f'attachment_{module}_{lang}'.replace('.', '_').replace(' ', '_'),
                        'model': 'ir.attachment',
                        'module': module,
                        'res_id': attachment.id,
                    })

        IrAsset = self.env['ir.asset']
        assets_vals = []

        # Generate 'ir.asset' record values for each asset delared in the manifest
        for bundle, commands in terp.get('assets', {}).items():
            for command in commands:
                directive, target, path = IrAsset._process_command(command)
                if is_wildcard_glob(path):
                    raise UserError(_(
                        "The assets path in the manifest of imported module '%(module_name)s' "
                        "cannot contain glob wildcards (e.g., *, **).", module_name=module))
                path = path if path.startswith('/') else '/' + path # Ensures a '/' at the start
                assets_vals.append({
                    'name': f'{module}.{bundle}.{path}',
                    'directive': directive,
                    'target': target,
                    'path': path,
                    'bundle': bundle,
                })

        # Look for existing assets
        existing_assets = {
            asset.name: asset
            for asset in IrAsset.search([('name', 'in', [vals['name'] for vals in assets_vals])])
        }
        assets_to_create = []

        # Update existing assets and generate the list of new assets values
        for values in assets_vals:
            if values['name'] in existing_assets:
                existing_assets[values['name']].write(values)
            else:
                assets_to_create.append(values)

        # Create new assets and attach 'ir.model.data' records to them
        created_assets = IrAsset.create(assets_to_create)
        self.env['ir.model.data'].create([{
            'name': f"{asset['bundle']}_{asset['path']}".replace(".", "_"),
            'model': 'ir.asset',
            'module': module,
            'res_id': asset.id,
        } for asset in created_assets])

        self.env['ir.module.module']._load_module_terms(
            [module],
            [lang for lang, _name in self.env['res.lang'].get_installed()],
            overwrite=True,
        )

        if ('knowledge.article' in self.env
            and (article_record := self.env.ref(f"{module}.welcome_article", raise_if_not_found=False))
            and article_record._name == 'knowledge.article'
            and self.env.ref(f"{module}.welcome_article_body", raise_if_not_found=False)
        ):
            body = self.env['ir.qweb']._render(f"{module}.welcome_article_body", lang=self.env.user.lang)
            article_record.write({'body': body})

        mod._update_from_terp(terp)
        _logger.info("Successfully imported module '%s'", module)

        if force_website_id:
            # Restore neutralized website_id.
            request.session['force_website_id'] = force_website_id

        return True