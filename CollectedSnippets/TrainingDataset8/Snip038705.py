def test_bad_theme(self):
        df = pd.DataFrame(
            {"index": [date(2019, 8, 9), date(2019, 8, 10)], "numbers": [1, 10]}
        ).set_index("index")

        chart = altair._generate_chart(ChartType.LINE, df)
        with self.assertRaises(StreamlitAPIException) as exc:
            st._arrow_altair_chart(chart, theme="bad_theme")

        self.assertEqual(
            f'You set theme="bad_theme" while Streamlit charts only support theme=”streamlit” or theme=None to fallback to the default library theme.',
            str(exc.exception),
        )