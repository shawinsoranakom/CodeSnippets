def assert_json(self, content_to_assert: dict | list, test_name: str, subfolder='', force_save=False):
        """
        Helper to save/assert a dictionary to a JSON file located in the corresponding module `test_files`.
        By default, this method will assert the dictionary with the JSON content.
        To switch to save mode, add a `SAVE_JSON` tag when calling the test;
        the `content_to_assert` dictionary will then be written in to the test file.

        Before asserting, the dictionary will first be serialized to ensure it is in the same format of the saved JSON.
        This means that for example: all tuples within the dictionary will be converted to list, etc.

        :param content_to_assert: dictionary | list to save or assert to the corresponding test file
        :param test_name: the test file name
        :param subfolder: the test file subfolder(s), separated by `/` if there is more than one
        :param force_save: force the assert method to save the XML to the test file instead of asserting it
        """
        json_path = self._get_test_file_path(f"{test_name}.json", subfolder=subfolder)
        content_to_assert = json.loads(json.dumps(content_to_assert))
        if json_ignore_schema := self._get_json_ignore_schema(subfolder):
            self._apply_json_ignore_schema(content_to_assert, json_ignore_schema)

        if 'SAVE_JSON' in (config['test_tags'] or '').split(',') or force_save:
            with file_open(json_path, 'w') as f:
                f.write(json.dumps(content_to_assert, indent=4))
            _logger.info("Saved the generated JSON content to %s", json_path)
        else:
            with file_open(json_path, 'rb') as f:
                expected_content = json.loads(f.read())
            try:
                self.assertDictEqual(content_to_assert, expected_content)
            except AssertionError:
                if not force_save and 'SAVE_JSON_ON_FAIL' in config['test_tags']:
                    self.assert_json(content_to_assert=content_to_assert, test_name=test_name, subfolder=subfolder, force_save=True)
                else:
                    raise