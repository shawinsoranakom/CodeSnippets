def test_data_type(self):
        """Test that NumberInput.type is set to the proper
        NumberInput.DataType value
        """
        st.number_input("Label", value=0)
        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(NumberInput.INT, c.data_type)

        st.number_input("Label", value=0.5)
        c = self.get_delta_from_queue().new_element.number_input
        self.assertEqual(NumberInput.FLOAT, c.data_type)