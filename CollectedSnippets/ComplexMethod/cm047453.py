def _test_manifest_values(self, manifest_data: Manifest):
        module = manifest_data.name
        verified_keys = [
            'application', 'auto_install',
            'summary', 'description', 'author',
            'demo', 'data', 'test',
            # todo installable ?
        ]

        if len(manifest_data.get('countries', [])) == 1 and 'l10n' not in module:
            _logger.warning(
                "Module %r specific to one single country %r should contain `l10n` in their name.",
                module, manifest_data['countries'][0])

        for key, value in manifest_data._Manifest__manifest_content.items():
            if key in _DEFAULT_MANIFEST:
                if key in verified_keys:
                    self.assertNotEqual(
                       value,
                        _DEFAULT_MANIFEST[key],
                        f"Setting manifest key {key} to the default manifest value for module {module!r}. "
                        "You can remove this key from the dict to reduce noise/inconsistencies between manifests specifications"
                        " and ease understanding of manifest content."
                    )

                expected_type = type(_DEFAULT_MANIFEST[key])
                if not isinstance(value, expected_type):
                    if key != 'auto_install':
                        _logger.warning(
                            "Wrong type for manifest value %s in module %s, expected %s",
                            key, module, expected_type)
                    elif not isinstance(value, list):
                        _logger.warning(
                            "Wrong type for manifest value %s in module %s, expected bool or list",
                            key, module)
                else:
                    if key == 'countries':
                        self._test_manifest_countries_value(module, value)
            elif key == 'icon':
                self._test_manifest_icon_value(module, value)