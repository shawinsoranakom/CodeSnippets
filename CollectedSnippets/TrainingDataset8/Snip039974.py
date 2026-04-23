def test_color_picker_serde(self):
        cp = st.color_picker("cp", key="cp")
        check_roundtrip("cp", cp)