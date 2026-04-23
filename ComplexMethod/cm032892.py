def convert_matching_field(field_weight_str: str) -> str:
        tokens = field_weight_str.split("^")
        field = tokens[0]
        if field == "docnm_kwd" or field == "title_tks":
            field = "docnm@ft_docnm_rag_coarse"
        elif field == "title_sm_tks":
            field = "docnm@ft_docnm_rag_fine"
        elif field == "important_kwd":
            field = "important_keywords@ft_important_keywords_rag_coarse"
        elif field == "important_tks":
            field = "important_keywords@ft_important_keywords_rag_fine"
        elif field == "question_kwd":
            field = "questions@ft_questions_rag_coarse"
        elif field == "question_tks":
            field = "questions@ft_questions_rag_fine"
        elif field == "content_with_weight" or field == "content_ltks":
            field = "content@ft_content_rag_coarse"
        elif field == "content_sm_ltks":
            field = "content@ft_content_rag_fine"
        elif field == "authors_tks":
            field = "authors@ft_authors_rag_coarse"
        elif field == "authors_sm_tks":
            field = "authors@ft_authors_rag_fine"
        elif field == "tag_kwd":
            field = "tag_kwd@ft_tag_kwd_whitespace__"
        tokens[0] = field
        return "^".join(tokens)