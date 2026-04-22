def test_date_input_serde(self):
        date = st.date_input("date", key="date")
        check_roundtrip("date", date)

        date_interval = st.date_input(
            "date_interval",
            value=[datetime.now().date(), datetime.now().date() + timedelta(days=1)],
            key="date_interval",
        )
        check_roundtrip("date_interval", date_interval)