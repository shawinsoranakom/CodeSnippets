def test_checkbox_serde(self):
        cb = st.checkbox("cb", key="cb")
        check_roundtrip("cb", cb)