def test_xml_c14n2(self):
        datadir = findfile("c14n-20", subdir="xmltestdata")
        full_path = partial(os.path.join, datadir)

        files = [filename[:-4] for filename in sorted(os.listdir(datadir))
                 if filename.endswith('.xml')]
        input_files = [
            filename for filename in files
            if filename.startswith('in')
        ]
        configs = {
            filename: {
                # <c14n2:PrefixRewrite>sequential</c14n2:PrefixRewrite>
                option.tag.split('}')[-1]: ((option.text or '').strip(), option)
                for option in ET.parse(full_path(filename) + ".xml").getroot()
            }
            for filename in files
            if filename.startswith('c14n')
        }

        tests = {
            input_file: [
                (filename, configs[filename.rsplit('_', 1)[-1]])
                for filename in files
                if filename.startswith(f'out_{input_file}_')
                and filename.rsplit('_', 1)[-1] in configs
            ]
            for input_file in input_files
        }

        # Make sure we found all test cases.
        self.assertEqual(30, len([
            output_file for output_files in tests.values()
            for output_file in output_files]))

        def get_option(config, option_name, default=None):
            return config.get(option_name, (default, ()))[0]

        for input_file, output_files in tests.items():
            for output_file, config in output_files:
                keep_comments = get_option(
                    config, 'IgnoreComments') == 'true'  # no, it's right :)
                strip_text = get_option(
                    config, 'TrimTextNodes') == 'true'
                rewrite_prefixes = get_option(
                    config, 'PrefixRewrite') == 'sequential'
                if 'QNameAware' in config:
                    qattrs = [
                        f"{{{el.get('NS')}}}{el.get('Name')}"
                        for el in config['QNameAware'][1].findall(
                            '{http://www.w3.org/2010/xml-c14n2}QualifiedAttr')
                    ]
                    qtags = [
                        f"{{{el.get('NS')}}}{el.get('Name')}"
                        for el in config['QNameAware'][1].findall(
                            '{http://www.w3.org/2010/xml-c14n2}Element')
                    ]
                else:
                    qtags = qattrs = None

                # Build subtest description from config.
                config_descr = ','.join(
                    f"{name}={value or ','.join(c.tag.split('}')[-1] for c in children)}"
                    for name, (value, children) in sorted(config.items())
                )

                with self.subTest(f"{output_file}({config_descr})"):
                    if input_file == 'inNsRedecl' and not rewrite_prefixes:
                        self.skipTest(
                            f"Redeclared namespace handling is not supported in {output_file}")
                    if input_file == 'inNsSuperfluous' and not rewrite_prefixes:
                        self.skipTest(
                            f"Redeclared namespace handling is not supported in {output_file}")
                    if 'QNameAware' in config and config['QNameAware'][1].find(
                            '{http://www.w3.org/2010/xml-c14n2}XPathElement') is not None:
                        self.skipTest(
                            f"QName rewriting in XPath text is not supported in {output_file}")

                    f = full_path(input_file + ".xml")
                    if input_file == 'inC14N5':
                        # Hack: avoid setting up external entity resolution in the parser.
                        with open(full_path('world.txt'), 'rb') as entity_file:
                            with open(f, 'rb') as f:
                                f = io.BytesIO(f.read().replace(b'&ent2;', entity_file.read()))

                    text = ET.canonicalize(
                        from_file=f,
                        with_comments=keep_comments,
                        strip_text=strip_text,
                        rewrite_prefixes=rewrite_prefixes,
                        qname_aware_tags=qtags, qname_aware_attrs=qattrs)

                    with open(full_path(output_file + ".xml"), 'r', encoding='utf8') as f:
                        expected = f.read()
                        if input_file == 'inC14N3':
                            # FIXME: cET resolves default attributes but ET does not!
                            expected = expected.replace(' attr="default"', '')
                            text = text.replace(' attr="default"', '')
                    self.assertEqual(expected, text)