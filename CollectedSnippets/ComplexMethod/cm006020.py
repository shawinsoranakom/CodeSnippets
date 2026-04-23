def test_clean_data_with_stringify(self, component_class):
        # Arrange
        data_frame = DataFrame(
            {
                "Name": ["John", "Jane\n", "\nBob"],
                "Age": [30, None, 25],
                "Notes": ["Good\n\nPerson", "", "Nice\n"],
            }
        )
        kwargs = {
            "input_data": data_frame,
            "mode": "Stringify",
            "clean_data": True,
        }
        component = component_class(**kwargs)

        # Act
        result = component.parse_combined_text()

        # Assert
        assert isinstance(result, Message)
        # Check for table structure
        assert "| Name" in result.text
        assert "|   Age" in result.text
        assert "| Notes" in result.text
        # Check for cleaned data
        assert "| John" in result.text
        assert "| Jane" in result.text
        assert "| Bob" in result.text
        assert "| Good" in result.text
        assert "| Person" in result.text
        assert "| Nice" in result.text
        # Verify data is cleaned
        assert "Jane\n" not in result.text
        assert "\nBob" not in result.text
        assert "Good\n\nPerson" not in result.text
        assert "Nice\n" not in result.text