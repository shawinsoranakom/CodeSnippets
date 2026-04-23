def test_pyspark_dataframe_write(self):
        """Test st.write with pyspark.sql.DataFrame."""

        # PySpark DataFrame should call streamlit.delta_generator.DeltaGenerator.dataframe
        with patch("streamlit.delta_generator.DeltaGenerator.dataframe") as p:
            snowpark_dataframe = (
                pyspark_mocks.create_pyspark_dataframe_with_mocked_personal_data()
            )
            st.write(snowpark_dataframe)
            p.assert_called_once()