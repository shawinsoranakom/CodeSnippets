def test_correct_ODOO_MODULE_RE(self):
        cases = [
            '// @odoo-module',
            '//@odoo-module',
            '/* @odoo-module',
            '/** @odoo-module',
            '/*@odoo-module',
            '/**@odoo-module',
            '// @odoo-module alias=web.test',
            '/* @odoo-module  alias=web.test',
            '/** @odoo-module  alias=web.test',
            '/** @odoo-module  alias=web.test**/',
            '/* @odoo-module  alias=web.test ',
            '/* @odoo-module alias=web.test default=false',
            '/* @odoo-module alias=web.test default=false ',
            '/* @odoo-module alias=web.test default=false**/',
        ]

        for case in cases:
            assert ODOO_MODULE_RE.match(case), "URL_RE is failing... >%s<" % case
            if "alias" in case:
                assert ODOO_MODULE_RE.match(case).groupdict().get('alias'), "URL_RE is failing for alias... >%s<" % case
                assert ODOO_MODULE_RE.match(case).groupdict().get('alias') == "web.test", "URL_RE does not get the right alias for ... >%s<" % case
            if "default" in case:
                assert ODOO_MODULE_RE.match(case).groupdict().get('default'), "URL_RE is failing for default... >%s<" % case
                assert ODOO_MODULE_RE.match(case).groupdict().get('default') == "false", "URL_RE does not get the right default for ... >%s<" % case