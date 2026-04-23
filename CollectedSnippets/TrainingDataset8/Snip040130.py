def test_data_frame_with_dtype_values_to_bytes(self):
        df1 = pd.DataFrame(["foo", "bar"])
        df2 = pd.DataFrame(df1.dtypes)

        try:
            data_frame_to_bytes(df2)
        except Exception as ex:
            self.fail(f"Converting dtype dataframes to Arrow should not fail: {ex}")