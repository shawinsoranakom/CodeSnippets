def test_get_latest_streamlit_version(self):
        with requests_mock.mock() as m:
            m.get(PYPI_STREAMLIT_URL, json={"info": {"version": "1.2.3"}})
            self.assertEqual(PkgVersion("1.2.3"), _get_latest_streamlit_version())