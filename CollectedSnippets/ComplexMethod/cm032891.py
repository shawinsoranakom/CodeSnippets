def convert_select_fields(self, output_fields: list[str]) -> list[str]:
        need_empty_count = "important_kwd" in output_fields
        for i, field in enumerate(output_fields):
            if field in ["docnm_kwd", "title_tks", "title_sm_tks"]:
                output_fields[i] = "docnm"
            elif field in ["important_kwd", "important_tks"]:
                output_fields[i] = "important_keywords"
            elif field in ["question_kwd", "question_tks"]:
                output_fields[i] = "questions"
            elif field in ["content_with_weight", "content_ltks", "content_sm_ltks"]:
                output_fields[i] = "content"
            elif field in ["authors_tks", "authors_sm_tks"]:
                output_fields[i] = "authors"
        if need_empty_count and "important_kwd_empty_count" not in output_fields:
            output_fields.append("important_kwd_empty_count")
        return list(set(output_fields))