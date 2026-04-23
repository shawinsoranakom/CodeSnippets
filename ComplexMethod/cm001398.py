def ask_yes_no(self, question: str, default: bool | None = None) -> str:
        """Ask the user a yes/no question.

        Args:
            question: The question to ask
            default: Optional default answer

        Returns:
            str: JSON with the user's answer (true/false)
        """
        if default is True:
            prompt_suffix = " [Y/n]"
        elif default is False:
            prompt_suffix = " [y/N]"
        else:
            prompt_suffix = " [y/n]"

        print(f"\nQ: {question}{prompt_suffix}")

        while True:
            resp = click.prompt("A", default="", show_default=False).strip().lower()

            if resp == "" and default is not None:
                answer = default
                break
            elif resp in ("y", "yes"):
                answer = True
                break
            elif resp in ("n", "no"):
                answer = False
                break
            else:
                print("Please enter 'y' or 'n'")

        return json.dumps(
            {
                "question": question,
                "answer": answer,
                "response": "yes" if answer else "no",
            }
        )