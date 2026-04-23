def concat_dataframes(df_list: list[pd.DataFrame], select_fields: list[str]) -> pd.DataFrame:
        df_list2 = [df for df in df_list if not df.empty]
        if df_list2:
            return pd.concat(df_list2, axis=0).reset_index(drop=True)

        schema = []
        for field_name in select_fields:
            if field_name == "score()":  # Workaround: fix schema is changed to score()
                schema.append("SCORE")
            elif field_name == "similarity()":  # Workaround: fix schema is changed to similarity()
                schema.append("SIMILARITY")
            elif field_name == "row_id()":  # Workaround: fix schema - Infinity returns "row_id" not "row_id()"
                schema.append("row_id")
            else:
                schema.append(field_name)
        return pd.DataFrame(columns=schema)