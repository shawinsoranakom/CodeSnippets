def evaluate_answer_correctness(extracted_answer, ground_truth):
        """Evaluate answer correctness with multiple criteria"""
        if not extracted_answer or not ground_truth:
            return False, False, 0.0

        norm_extracted = normalize_answer(extracted_answer)
        norm_ground_truth = normalize_answer(ground_truth)

        if norm_extracted == norm_ground_truth:
            return True, True, 1.0

        try:
            extracted_num = float(norm_extracted)
            ground_truth_num = float(norm_ground_truth)

            if ground_truth_num != 0:
                relative_error = abs(extracted_num - ground_truth_num) / abs(
                    ground_truth_num
                )

                if relative_error < 0.01:
                    return True, True, 0.9
                elif relative_error < 0.05:
                    return False, True, 0.7
                elif relative_error < 0.10:
                    return False, True, 0.5
            else:
                if extracted_num == 0:
                    return True, True, 1.0
                elif abs(extracted_num) < 0.01:
                    return False, True, 0.7

        except (ValueError, TypeError):
            if norm_extracted.lower() == norm_ground_truth.lower():
                return True, True, 1.0

        return False, False, 0.0