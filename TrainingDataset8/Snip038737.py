def test_pandas_version_below_1_3_0(self, mock_styler_translate):
        """Tests that `styler._translate` is called without arguments in Pandas < 1.3.0"""
        df = mock_data_frame()
        styler = df.style.set_uuid("FAKE_UUID")

        st._arrow_table(styler)
        mock_styler_translate.assert_called_once_with()