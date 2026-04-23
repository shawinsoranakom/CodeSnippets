def test_text_area_serde(self):
        text_area = st.text_area("text_area", key="text_area")
        check_roundtrip("text_area", text_area)

        text_area_default = st.text_area(
            "text_area_default",
            value="default",
            key="text_area_default",
        )
        check_roundtrip("text_area_default", text_area_default)