def test_step_zero(self):
        with pytest.raises(StreamlitAPIException) as exc:
            st.slider("Label", min_value=0, max_value=10, step=0)
        self.assertEqual(
            "Slider components cannot be passed a `step` of 0.", str(exc.value)
        )