def test_just_label(self):
        """Test that it can be called with no value."""
        st.date_input("the label")

        c = self.get_delta_from_queue().new_element.date_input
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertLessEqual(
            datetime.strptime(c.default[0], "%Y/%m/%d").date(), datetime.now().date()
        )
        self.assertEqual(c.disabled, False)