def _compute_arch(self):
        def resolve_external_ids(arch_fs, view_xml_id):
            def replacer(m):
                xmlid = m.group('xmlid')
                if '.' not in xmlid:
                    xmlid = '%s.%s' % (view_xml_id.split('.')[0], xmlid)
                return m.group('prefix') + str(self.env['ir.model.data']._xmlid_to_res_id(xmlid))
            return re.sub(r'(?P<prefix>[^%])%\((?P<xmlid>.*?)\)[ds]', replacer, arch_fs)

        lang = self.env.lang or 'en_US'
        env_en = self.with_context(edit_translations=None, lang='en_US', check_translations=True).env
        env_lang = self.with_context(lang=lang, check_translations=True).env
        field_arch_db = self._fields['arch_db']
        for view in self:
            arch_fs = None
            read_file = self.env.context.get('read_arch_from_file') or \
                ('xml' in config['dev_mode'] and not view.arch_updated)
            if read_file and view.arch_fs and (view.xml_id or view.key):
                xml_id = view.xml_id or view.key
                try:
                    # reading the file will raise an OSError if it is unreadable
                    arch_fs = get_view_arch_from_file(file_path(view.arch_fs, check_exists=False), xml_id)
                except OSError:
                    _logger.warning("View %s: Full path [%s] cannot be found.", xml_id, view.arch_fs)
                    arch_fs = False

                # replace %(xml_id)s, %(xml_id)d, %%(xml_id)s, %%(xml_id)d by the res_id
                if arch_fs:
                    arch_fs = resolve_external_ids(arch_fs, xml_id).replace('%%', '%')
                    translation_dictionary = field_arch_db.get_translation_dictionary(
                        view.with_env(env_en).arch_db, {lang: view.with_env(env_lang).arch_db}
                    )
                    arch_fs = field_arch_db.translate(
                        lambda term: translation_dictionary[term][lang],
                        arch_fs
                    )
            view.arch = arch_fs or view.arch_db