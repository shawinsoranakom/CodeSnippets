def test_bad_theme(self):
        with self.assertRaises(StreamlitAPIException) as exc:
            st._arrow_altair_chart(df1, theme="bad_theme")

        self.assertEqual(
            f'You set theme="bad_theme" while Streamlit charts only support theme=”streamlit” or theme=None to fallback to the default library theme.',
            str(exc.exception),
        )