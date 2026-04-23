def test_value_out_of_bounds(self):
        # Max int
        with pytest.raises(StreamlitAPIException) as exc:
            value = JSNumber.MAX_SAFE_INTEGER + 1
            st.number_input("Label", value=value)
        self.assertEqual(
            "`value` (%s) must be <= (1 << 53) - 1" % str(value), str(exc.value)
        )

        # Min int
        with pytest.raises(StreamlitAPIException) as exc:
            value = JSNumber.MIN_SAFE_INTEGER - 1
            st.number_input("Label", value=value)
        self.assertEqual(
            "`value` (%s) must be >= -((1 << 53) - 1)" % str(value), str(exc.value)
        )

        # Max float
        with pytest.raises(StreamlitAPIException) as exc:
            value = 2e308
            st.number_input("Label", value=value)
        self.assertEqual(
            "`value` (%s) must be <= 1.797e+308" % str(value), str(exc.value)
        )

        # Min float
        with pytest.raises(StreamlitAPIException) as exc:
            value = -2e308
            st.number_input("Label", value=value)
        self.assertEqual(
            "`value` (%s) must be >= -1.797e+308" % str(value), str(exc.value)
        )