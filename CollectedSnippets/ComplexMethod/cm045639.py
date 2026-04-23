def __call__(self, key, row, time, is_addition):
            self.n_processed_rows += 1
            column_values = known_rows[row["pkey"]]
            for field, expected_value in column_values.items():
                if isinstance(expected_value, np.ndarray):
                    assert row[field].shape == expected_value.shape
                    assert (row[field] == expected_value).all()
                else:
                    expected_values = [expected_value]
                    if data_format == "csv" and expected_value is None:
                        # Impossible to parse unambiguosly, hence allowing string "None"
                        # or base64-decoded option
                        if field == "string":
                            expected_values.append("None")
                        elif field == "binary_data":
                            expected_values.append(base64.b64decode("None"))

                    assert row[field] in expected_values