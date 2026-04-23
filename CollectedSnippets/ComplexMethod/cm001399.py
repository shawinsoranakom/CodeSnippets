def ask_choice(
        self, question: str, choices: list[str], allow_multiple: bool = False
    ) -> str:
        """Present choices to the user.

        Args:
            question: The question to ask
            choices: List of choices
            allow_multiple: Whether multiple selections are allowed

        Returns:
            str: JSON with selected choice(s)
        """
        print(f"\nQ: {question}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")

        if allow_multiple:
            print("Enter choice numbers separated by commas (e.g., '1,3,4'):")
        else:
            print("Enter choice number:")

        while True:
            resp = click.prompt("A", default="", show_default=False).strip()

            try:
                if allow_multiple:
                    indices = [int(x.strip()) for x in resp.split(",")]
                    if all(1 <= i <= len(choices) for i in indices):
                        selected = [choices[i - 1] for i in indices]
                        return json.dumps(
                            {
                                "question": question,
                                "selected": selected,
                                "indices": indices,
                            }
                        )
                else:
                    index = int(resp)
                    if 1 <= index <= len(choices):
                        selected = choices[index - 1]
                        return json.dumps(
                            {"question": question, "selected": selected, "index": index}
                        )

                print(f"Please enter a valid number between 1 and {len(choices)}")

            except ValueError:
                print("Please enter a valid number")