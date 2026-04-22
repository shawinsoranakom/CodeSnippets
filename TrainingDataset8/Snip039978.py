def test_number_input_serde(self):
        number = st.number_input("number", key="number")
        check_roundtrip("number", number)

        number_int = st.number_input("number_int", value=16777217, key="number_int")
        check_roundtrip("number_int", number_int)