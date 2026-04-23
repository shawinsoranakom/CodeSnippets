def test_pandas_serialization(self) -> None:
        """Test serialization of pandas DataFrame."""
        # Test DataFrame
        test_df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"], "C": [1.1, 2.2, 3.3]})
        result = serialize(test_df)
        assert isinstance(result, list)  # DataFrame is serialized to list of records
        assert len(result) == 3
        assert all(isinstance(row, dict) for row in result)
        assert all("A" in row and "B" in row and "C" in row for row in result)
        assert result[0] == {"A": 1, "B": "a", "C": 1.1}

        # Test DataFrame truncation
        df_long = pd.DataFrame({"A": range(MAX_ITEMS_LENGTH + 100)})
        result = serialize(df_long, max_items=MAX_ITEMS_LENGTH)
        assert isinstance(result, list)
        assert len(result) == MAX_ITEMS_LENGTH
        assert all("A" in row for row in result)