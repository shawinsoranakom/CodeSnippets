def get_fields(self, res: tuple[pd.DataFrame, int] | pd.DataFrame, fields: list[str]) -> dict[str, dict]:
        if isinstance(res, tuple):
            res = res[0]
        if not fields:
            return {}
        fields_all = fields.copy()
        fields_all.append("id")
        fields_all = set(fields_all)
        if "docnm" in res.columns:
            for field in ["docnm_kwd", "title_tks", "title_sm_tks"]:
                if field in fields_all:
                    res[field] = res["docnm"]
        if "important_keywords" in res.columns:
            if "important_kwd" in fields_all:
                if "important_kwd_empty_count" in res.columns:
                    base = res["important_keywords"].apply(lambda raw: raw.split(",") if raw else [])
                    counts = res["important_kwd_empty_count"].fillna(0).astype(int)
                    res["important_kwd"] = [
                        tokens + [""] * empty_count
                        for tokens, empty_count in zip(base.tolist(), counts.tolist())
                    ]
                else:
                    res["important_kwd"] = res["important_keywords"].apply(lambda v: v.split(",") if v else [])
            if "important_tks" in fields_all:
                res["important_tks"] = res["important_keywords"]
        if "questions" in res.columns:
            if "question_kwd" in fields_all:
                res["question_kwd"] = res["questions"].apply(lambda v: v.splitlines())
            if "question_tks" in fields_all:
                res["question_tks"] = res["questions"]
        if "content" in res.columns:
            for field in ["content_with_weight", "content_ltks", "content_sm_ltks"]:
                if field in fields_all:
                    res[field] = res["content"]
        if "authors" in res.columns:
            for field in ["authors_tks", "authors_sm_tks"]:
                if field in fields_all:
                    res[field] = res["authors"]

        column_map = {col.lower(): col for col in res.columns}
        # row_id() is returned by infinity as "row_id", add mapping for lookup
        if "row_id()" in fields_all and "row_id" in column_map:
            column_map["row_id()"] = column_map["row_id"]
        matched_columns = {column_map[col.lower()]: col for col in fields_all if col.lower() in column_map}
        none_columns = [col for col in fields_all if col.lower() not in column_map]

        res2 = res[matched_columns.keys()]
        res2 = res2.rename(columns=matched_columns)
        res2.drop_duplicates(subset=["id"], inplace=True)

        for column in list(res2.columns):
            k = column.lower()
            if self.field_keyword(k):
                res2[column] = res2[column].apply(lambda v: [kwd for kwd in v.split("###") if kwd])
            elif re.search(r"_feas$", k):
                res2[column] = res2[column].apply(lambda v: json.loads(v) if v else {})
            elif k == "chunk_data":
                # Parse JSON data back to dict for table parser fields
                res2[column] = res2[column].apply(lambda v: json.loads(v) if v and isinstance(v, str) else v)
            elif k == "position_int":
                def to_position_int(v):
                    if v:
                        arr = [int(hex_val, 16) for hex_val in v.split("_")]
                        v = [arr[i: i + 5] for i in range(0, len(arr), 5)]
                    else:
                        v = []
                    return v

                res2[column] = res2[column].apply(to_position_int)
            elif k in ["page_num_int", "top_int"]:
                res2[column] = res2[column].apply(lambda v: [int(hex_val, 16) for hex_val in v.split("_")] if v else [])
            else:
                pass
        for column in ["docnm", "important_keywords", "questions", "content", "authors"]:
            if column in res2:
                del res2[column]
        for column in none_columns:
            res2[column] = None

        return res2.set_index("id").to_dict(orient="index")