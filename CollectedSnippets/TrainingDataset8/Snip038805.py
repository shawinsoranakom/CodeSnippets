def test_value_in_range(self, value, min_date, max_date):
        st.date_input("the label", value=value, min_value=min_date, max_value=max_date)