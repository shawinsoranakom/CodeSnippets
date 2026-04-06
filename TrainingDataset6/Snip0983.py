def test_get_output_unicode_misspell(self, wait_output_mock):
        rerun.get_output(u'pácman', u'pácman')
        wait_output_mock.assert_called_once()