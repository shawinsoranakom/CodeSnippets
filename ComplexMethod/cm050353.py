def _import_zipfile(self, module_file, force=False, with_demo=False):
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can install data modules."))
        if not module_file:
            raise Exception(_("No file sent."))
        if not zipfile.is_zipfile(module_file):
            raise UserError(_('Only zip files are supported.'))

        module_names = []
        with zipfile.ZipFile(module_file, "r") as z:
            for zf in z.infolist():
                if zf.file_size > MAX_FILE_SIZE:
                    raise UserError(_("File '%s' exceed maximum allowed file size", zf.filename))

            with file_open_temporary_directory(self.env) as module_dir:
                manifest_files = sorted(
                    (file.filename.split('/')[0], file)
                    for file in z.infolist()
                    if file.filename.count('/') == 1
                    and file.filename.split('/')[1] in MANIFEST_NAMES
                )
                module_data_files = defaultdict(list)
                dependencies = defaultdict(list)
                for mod_name, manifest in manifest_files:
                    _manifest_path = z.extract(manifest, module_dir)
                    terp = Manifest._from_path(opj(module_dir, mod_name), env=self.env)
                    if not terp:
                        continue
                    files_to_import = terp.get('data', []) + terp.get('init_xml', []) + terp.get('update_xml', [])
                    if with_demo:
                        files_to_import += terp.get('demo', [])
                    for filename in files_to_import:
                        if os.path.splitext(filename)[1].lower() not in ('.xml', '.csv', '.sql'):
                            continue
                        module_data_files[mod_name].append('%s/%s' % (mod_name, filename))
                    dependencies[mod_name] = terp.get('depends', [])

                dirs = {d for d in os.listdir(module_dir) if os.path.isdir(opj(module_dir, d))}
                sorted_dirs = topological_sort(dependencies)
                if wrong_modules := dirs.difference(sorted_dirs):
                    raise UserError(_(
                        "No manifest found in '%(modules)s'. Can't import the zip file.",
                        modules=", ".join(wrong_modules)
                    ))

                for file in z.infolist():
                    filename = file.filename
                    mod_name = filename.split('/')[0]
                    is_data_file = filename in module_data_files[mod_name]
                    is_static = filename.startswith('%s/static' % mod_name)
                    is_translation = filename.startswith('%s/i18n' % mod_name) and filename.endswith('.po')
                    if is_data_file or is_static or is_translation:
                        z.extract(file, module_dir)

                for mod_name in sorted_dirs:
                    module_names.append(mod_name)
                    try:
                        # assert mod_name.startswith('theme_')
                        path = opj(module_dir, mod_name)
                        self.sudo()._import_module(mod_name, path, force=force, with_demo=with_demo)
                    except Exception as e:
                        raise UserError(_(
                            "Error while importing module '%(module)s'.\n\n %(error_message)s \n\n",
                            module=mod_name, error_message=traceback.format_exc(),
                        )) from e
        return "", module_names