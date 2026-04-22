def test_is_snowpark_dataframe(self):
        df = pd.DataFrame(
            {
                "mixed-integer": [1, "foo", 3],
                "mixed": [1.0, "foo", 3],
                "complex": [1 + 2j, 3 + 4j, 5 + 6 * 1j],
                "integer": [1, 2, 3],
                "float": [1.0, 2.1, 3.2],
                "string": ["foo", "bar", None],
            },
            index=[1.0, "foo", 3],
        )

        # pandas dataframe should not be SnowparkDataFrame
        self.assertFalse(is_snowpark_data_object(df))

        # if snowflake.snowpark.dataframe.DataFrame def is_snowpark_data_object should return true
        self.assertTrue(is_snowpark_data_object(DataFrame()))

        # any object should not be snowpark dataframe
        self.assertFalse(is_snowpark_data_object("any text"))
        self.assertFalse(is_snowpark_data_object(123))

        class DummyClass:
            """DummyClass for testing purposes"""

        self.assertFalse(is_snowpark_data_object(DummyClass()))

        # empty list should not be snowpark dataframe
        self.assertFalse(is_snowpark_data_object(list()))

        # list with items should not be snowpark dataframe
        self.assertFalse(
            is_snowpark_data_object(
                [
                    "any text",
                ]
            )
        )
        self.assertFalse(
            is_snowpark_data_object(
                [
                    123,
                ]
            )
        )
        self.assertFalse(
            is_snowpark_data_object(
                [
                    DummyClass(),
                ]
            )
        )
        self.assertFalse(
            is_snowpark_data_object(
                [
                    df,
                ]
            )
        )

        # list with SnowparkRow should be SnowparkDataframe
        self.assertTrue(
            is_snowpark_data_object(
                [
                    Row(),
                ]
            )
        )