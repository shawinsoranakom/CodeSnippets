def _test_normalized_data(self, testdata):
        prefix = "normalized_"
        partner = self.env['res.partner'].create({'name': 'partner'})
        for testentry in testdata:
            with self.subTest(testentry=testentry):
                partner.write({
                    k: (v if isinstance(v, str | int | float) else v.id)
                    for k, v in testentry.items()
                    if not k.startswith(prefix)
                })
                l10n_it_edi_values = partner._l10n_it_edi_get_values()
                for field, expected in [
                    (k[len(prefix):], v)
                    for k, v in testentry.items()
                    if k.startswith(prefix)
                ]:
                    self.assertEqual(expected, l10n_it_edi_values.get(field))