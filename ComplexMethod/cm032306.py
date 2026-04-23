def get_fields(self, res: tuple[pd.DataFrame, int] | pd.DataFrame, fields: list[str]) -> dict[str, dict]:
        if isinstance(res, tuple):
            res_df = res[0]
        else:
            res_df = res
        if not fields:
            return {}
        fields_all = fields.copy()
        fields_all.append("id")
        fields_all = self.convert_select_fields(fields_all, res_df.columns.tolist())

        column_map = {col.lower(): col for col in res_df.columns}
        matched_columns = {column_map[col.lower()]: col for col in fields_all if col.lower() in column_map}
        none_columns = [col for col in fields_all if col.lower() not in column_map]

        selected_res = res_df[matched_columns.keys()]
        selected_res = selected_res.rename(columns=matched_columns)
        selected_res.drop_duplicates(subset=["id"], inplace=True)

        for column in list(selected_res.columns):
            k = column.lower()
            if self.field_keyword(k):
                selected_res[column] = selected_res[column].apply(lambda v: [kwd for kwd in v.split("###") if kwd])
            else:
                pass

        for column in none_columns:
            selected_res[column] = None

        res_dict = selected_res.set_index("id").to_dict(orient="index")
        return {_id: {self.convert_infinity_field_to_message(k): v for k, v in doc.items()} for _id, doc in res_dict.items()}