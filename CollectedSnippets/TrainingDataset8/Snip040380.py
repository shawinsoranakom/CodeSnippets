def test_snowpark_dataframe_write(self):
        """Test st.write with snowflake.snowpark.dataframe.DataFrame."""

        # SnowparkDataFrame should call streamlit.delta_generator.DeltaGenerator.dataframe
        with patch("streamlit.delta_generator.DeltaGenerator.dataframe") as p:
            st.write(DataFrame())
            p.assert_called_once()

        # SnowparkRow inside list should call streamlit.delta_generator.DeltaGenerator.dataframe
        with patch("streamlit.delta_generator.DeltaGenerator.dataframe") as p:
            st.write(
                [
                    Row(),
                ]
            )
            p.assert_called_once()