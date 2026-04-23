def test_select_slider_serde(self):
        select_slider = st.select_slider(
            "select_slider", options=["a", "b", "c"], key="select_slider"
        )
        check_roundtrip("select_slider", select_slider)

        select_slider_range = st.select_slider(
            "select_slider_range",
            options=["a", "b", "c"],
            value=["a", "b"],
            key="select_slider_range",
        )
        check_roundtrip("select_slider_range", select_slider_range)