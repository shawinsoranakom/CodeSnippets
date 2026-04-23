def score_column(col_name, keywords, role_type, num_candidates):
        """Score a column for how likely it is to be a particular role."""
        if not has_keyword(col_name, keywords):
            return 0

        score = 0
        score += 10

        # Penalize ambiguous keywords when scoring for user
        if role_type == "user":
            col_lower = col_name.lower()
            # If column is ONLY "task" (or task_xxx), give it lower priority for user role
            if "task" in col_lower and not any(
                kw in col_lower for kw in user_words_high_priority
            ):
                score -= 15  # Significant penalty so other user columns win

        priority_bonus = get_priority_score(col_name)
        score += priority_bonus

        if role_type in ["assistant", "user"]:
            avg_length = get_content_length(col_name)

            if num_candidates > 1:
                if avg_length > 1000:
                    score += 50
                elif avg_length > 200:
                    score += 30
                elif avg_length > 50:
                    score += 10
                elif avg_length < 50:
                    score -= 20
            else:
                if avg_length > 1000:
                    score += 50
                elif avg_length > 200:
                    score += 30
                elif avg_length > 50:
                    score += 10

        return score