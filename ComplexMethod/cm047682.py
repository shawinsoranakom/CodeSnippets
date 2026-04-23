def _export_translatable_resources(self):
        """ Export translations for static terms

        This will include:
        - the python strings marked with _() or _lt()
        - the javascript strings marked with _t() inside static/src/js/
        - the strings inside Qweb files inside static/src/xml/
        - the spreadsheet data files
        """

        # Also scan these non-addon paths
        for bin_path in ['orm', 'osv', 'report', 'modules', 'service', 'tools']:
            self._path_list.append((os.path.join(config.root_path, bin_path), True))
        # non-recursive scan for individual files in root directory but without
        # scanning subdirectories that may contain addons
        self._path_list.append((config.root_path, False))
        _logger.debug("Scanning modules at paths: %s", self._path_list)

        spreadsheet_files_regex = re.compile(r".*_dashboard(\.osheet)?\.json$")

        for (path, recursive) in self._path_list:
            _logger.debug("Scanning files of modules at %s", path)
            for root, _dummy, files in os.walk(path, followlinks=True):
                for fname in fnmatch.filter(files, '*.py'):
                    self._babel_extract_terms(fname, path, root, 'odoo.tools.babel:extract_python',
                                              extra_comments=[PYTHON_TRANSLATION_COMMENT],
                                              extract_keywords={'_': None, '_lt': None})
                if fnmatch.fnmatch(root, '*/static/src*'):
                    # Javascript source files
                    for fname in fnmatch.filter(files, '*.js'):
                        self._babel_extract_terms(fname, path, root, 'odoo.tools.babel:extract_javascript',
                                                  extra_comments=[JAVASCRIPT_TRANSLATION_COMMENT],
                                                  extract_keywords={'_t': None})
                    # QWeb template files
                    for fname in fnmatch.filter(files, '*.xml'):
                        self._babel_extract_terms(fname, path, root, 'odoo.tools.translate:babel_extract_qweb',
                                                  extra_comments=[JAVASCRIPT_TRANSLATION_COMMENT])
                if fnmatch.fnmatch(root, '*/data/*'):
                    for fname in filter(spreadsheet_files_regex.match, files):
                        self._babel_extract_terms(fname, path, root, 'odoo.tools.translate:extract_spreadsheet_terms',
                                                  extra_comments=[JAVASCRIPT_TRANSLATION_COMMENT])
                if not recursive:
                    # due to topdown, first iteration is in first level
                    break

        IrModuleModule = self.env['ir.module.module']
        for module in self._modules:
            for translation in IrModuleModule._extract_resource_attachment_translations(module, self._lang):
                self._push_translation(*translation)