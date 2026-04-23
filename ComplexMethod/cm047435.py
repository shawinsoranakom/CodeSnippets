def test_incorrect_ODOO_MODULE_RE(self):
        cases = [
            '/* @odoo-module alias = web.test ',
            '/* @odoo-module alias= web.test',
            '/* @odoo-module alias = web.test default=false'
        ]

        for case in cases:
            assert not ODOO_MODULE_RE.match(case).groupdict().get('alias'), "URL_RE should fail because of too much spaces but didn't... >%s<" % case

        cases = [
            '// @odoo-modulealias=web.test',
            '/* @odoo-module alias=web.testdefault=false',
        ]

        for case in cases:
            if "alias" in case and "default" in case:
                assert \
                    not ODOO_MODULE_RE.match(case).groupdict().get('alias') \
                    or \
                    not ODOO_MODULE_RE.match(case).groupdict().get('default'), "URL_RE should fail for alias and default... >%s<" % case
            elif "alias" in case:
                assert not ODOO_MODULE_RE.match(case).groupdict().get('alias'), "URL_RE should fail for alias... >%s<" % case