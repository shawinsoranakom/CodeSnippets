def check_numbers(prompts, completions, answer, **kwargs):
        question = prompts[0][-1]["content"]
        responses = [completion[0]["content"] for completion in completions]

        extracted_responses = [
            guess.group(1) if (guess := match_numbers.search(r)) is not None else None
            for r in responses
        ]

        scores = []
        # Print only every few steps
        global PRINTED_TIMES
        global PRINT_EVERY_STEPS
        if PRINTED_TIMES % PRINT_EVERY_STEPS == 0:
            print(
                "*" * 20,
                f"Question:\n{question}",
                f"\nAnswer:\n{answer[0]}",
                f"\nResponse:\n{responses[0]}",
                f"\nExtracted:\n{extracted_responses[0]}",
            )
        PRINTED_TIMES += 1

        for guess, true_answer in zip(extracted_responses, answer):
            if guess is None:
                scores.append(0)
                continue
            # Convert to numbers
            try:
                true_answer = float(true_answer.strip())
                # Remove commas like in 123,456
                guess = float(guess.strip().replace(",", ""))
                scores.append(1.5 if guess == true_answer else -0.5)
            except:
                scores.append(0)
                continue
        return scores