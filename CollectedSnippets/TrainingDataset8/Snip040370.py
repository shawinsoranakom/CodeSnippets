def test_dataframe(self):
        """Test st.write with dataframe."""
        data = {
            type_util._PANDAS_DF_TYPE_STR: pd.DataFrame(
                [[20, 30, 50]], columns=["a", "b", "c"]
            ),
            type_util._PANDAS_SERIES_TYPE_STR: pd.Series(np.array(["a", "b", "c"])),
            type_util._PANDAS_INDEX_TYPE_STR: pd.Index(list("abc")),
            type_util._PANDAS_STYLER_TYPE_STR: pd.DataFrame(
                {"a": [1], "b": [2]}
            ).style.format("{:.2%}"),
            type_util._NUMPY_ARRAY_TYPE_STR: np.array(["a", "b", "c"]),
        }

        # Make sure we have test cases for all _DATAFRAME_LIKE_TYPES
        self.assertEqual(sorted(data.keys()), sorted(type_util._DATAFRAME_LIKE_TYPES))

        for df in data.values():
            with patch("streamlit.delta_generator.DeltaGenerator.dataframe") as p:
                st.write(df)

                p.assert_called_once()