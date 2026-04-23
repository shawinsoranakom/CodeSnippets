def assert_xml(
            self,
            xml_element: str | bytes | etree._Element,
            test_name: str,
            subfolder='',
            xpath_to_apply='',
            force_save=False,
    ):
        """
        Helper to save/assert an XML element/string/bytes to an XML file.
        By default, this method will assert the passed XML content to the test XML file.
        To switch to save mode, add a `SAVE_XML` tag when calling the test;
        This mode will instead do the following:

        - Reindent the XML element by `\t`
        - Save the XML element to a temporary folder for potential external testing
        - Patch the XML element with `___ignore___` values, following the corresponding schema on the closest `ignore_schema.xml`
        - Canonicalize the XML element to ensure consistency in their namespaces & attributes order
        - Save the XML element content to the test file

        :param xml_element: the _Element/str/bytes content to be saved or asserted
        :param test_name: the test file name
        :param subfolder: the test file subfolder(s), separated by `/` if there is more than one
        :param xpath_to_apply: optional `xpath` string to be applied on the expected file
        :param force_save: force the assert method to save the XML to the test file instead of asserting it
        :return:
        """
        file_name = f"{test_name}.xml"
        test_file_path = self._get_test_file_path(file_name, subfolder=subfolder)
        if isinstance(xml_element, str):
            xml_element = xml_element.encode()
        if isinstance(xml_element, bytes):
            xml_element = etree.fromstring(xml_element)

        if 'SAVE_XML' in (config['test_tags'] or '').split(',') or force_save:
            # Save the XML to tmp folder before modifying some elements with `___ignore___`
            etree.indent(xml_element, space='\t')
            with patch.object(re, 'fullmatch', lambda _arg1, _arg2: True):
                save_test_file(
                    test_name=test_name,
                    content=etree.tostring(xml_element, pretty_print=True, encoding='UTF-8'),
                    prefix=f"{self.test_module}",
                    extension='xml',
                    document_type='Invoice XML',
                    date_format='',
                )
            # Search for closest `ignore_schema.xml` from the file path and apply the change to xml_element
            xml_ignore_schema = self._get_xml_ignore_schema(subfolder)
            if xml_ignore_schema is not None:
                self._prepare_xml_ignore_schema(xml_ignore_schema)
                self._merge_two_xml(
                    xml_element,
                    xml_ignore_schema,
                    overwrite_on_conflict=True,
                    add_on_absent=False,
                )
                etree.indent(xml_element, space='\t')

            # Canonicalize & re-sort the namespaces
            canonicalized_xml_str = etree.canonicalize(xml_element)
            xml_element = etree.fromstring(canonicalized_xml_str)
            xml_element = self._rebuild_xml_with_sorted_namespaces(xml_element)

            # Save the xml_element content
            with file_open(test_file_path, 'wb') as f:
                f.write(etree.tostring(xml_element, pretty_print=True, encoding='UTF-8'))
                _logger.info("Saved the generated XML content to %s", file_name)
        else:
            with file_open(test_file_path, 'rb') as f:
                expected_xml_str = f.read()

            expected_xml_tree = etree.fromstring(expected_xml_str)
            if xpath_to_apply:
                expected_xml_tree = self.with_applied_xpath(expected_xml_tree, xpath_to_apply)
            try:
                self.assertXmlTreeEqual(xml_element, expected_xml_tree)
            except AssertionError:
                if not force_save and 'SAVE_XML_ON_FAIL' in config['test_tags']:
                    self.assert_xml(
                        xml_element=xml_element,
                        test_name=test_name,
                        subfolder=subfolder,
                        xpath_to_apply=xpath_to_apply,
                        force_save=True,
                    )
                else:
                    raise