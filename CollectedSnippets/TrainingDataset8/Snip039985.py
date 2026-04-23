def test_time_input_serde(self):
        time = st.time_input("time", key="time")
        check_roundtrip("time", time)

        time_datetime = st.time_input(
            "datetime",
            value=datetime.now(),
            key="time_datetime",
        )
        check_roundtrip("time_datetime", time_datetime)