def test_value_out_of_bounds(self):
        # Max int
        with pytest.raises(StreamlitAPIException) as exc:
            max_value = JSNumber.MAX_SAFE_INTEGER + 1
            st.slider("Label", max_value=max_value)
        self.assertEqual(
            "`max_value` (%s) must be <= (1 << 53) - 1" % str(max_value), str(exc.value)
        )

        # Min int
        with pytest.raises(StreamlitAPIException) as exc:
            min_value = JSNumber.MIN_SAFE_INTEGER - 1
            st.slider("Label", min_value=min_value)
        self.assertEqual(
            "`min_value` (%s) must be >= -((1 << 53) - 1)" % str(min_value),
            str(exc.value),
        )

        # Max float
        with pytest.raises(StreamlitAPIException) as exc:
            max_value = 2e308
            st.slider("Label", value=0.5, max_value=max_value)
        self.assertEqual(
            "`max_value` (%s) must be <= 1.797e+308" % str(max_value), str(exc.value)
        )

        # Min float
        with pytest.raises(StreamlitAPIException) as exc:
            min_value = -2e308
            st.slider("Label", value=0.5, min_value=min_value)
        self.assertEqual(
            "`min_value` (%s) must be >= -1.797e+308" % str(min_value), str(exc.value)
        )