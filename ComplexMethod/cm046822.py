def check_answer_correctness(prompts, completions, answer, **kwargs):
        """Reward function for answer correctness"""

        def extract_solution_answer(text):
            pattern = r"<answer>(.*?)</answer>"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return re.sub(r"[%$,]", "", match.group(1)).strip()
            return ""

        responses = [completion[0]["content"] for completion in completions]
        extracted_responses = [extract_solution_answer(r) for r in responses]

        scores = []
        for guess, true_answer in zip(extracted_responses, answer):
            score = 0
            if not guess:
                scores.append(0)
                continue

            if guess == true_answer:
                score += 3.0
            elif guess.strip() == true_answer.strip():
                score += 1.5
            else:
                try:
                    ratio = float(guess) / float(true_answer)
                    if 0.9 <= ratio <= 1.1:
                        score += 1.0
                    elif 0.8 <= ratio <= 1.2:
                        score += 0.5
                    else:
                        score -= 1.5
                except:
                    score -= 1.5
            scores.append(score)
        return scores