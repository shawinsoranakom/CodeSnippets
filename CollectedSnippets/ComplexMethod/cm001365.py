async def display_thoughts(
        self,
        ai_name: str,
        thoughts: "str | ModelWithSummary",
        speak_mode: bool = False,
    ) -> None:
        """Display the agent's thoughts.

        Args:
            ai_name: The name of the AI agent.
            thoughts: The agent's thoughts (string or structured).
            speak_mode: Whether to use text-to-speech.
        """
        from autogpt.agents.prompt_strategies.one_shot import AssistantThoughts

        from forge.models.utils import ModelWithSummary

        thoughts_text = self._remove_ansi_escape(
            thoughts.reasoning
            if isinstance(thoughts, AssistantThoughts)
            else (
                thoughts.summary()
                if isinstance(thoughts, ModelWithSummary)
                else thoughts
            )
        )
        print_attribute(
            f"{ai_name.upper()} THOUGHTS", thoughts_text, title_color=Fore.YELLOW
        )

        if isinstance(thoughts, AssistantThoughts):
            if assistant_thoughts_plan := self._remove_ansi_escape(
                "\n".join(f"- {p}" for p in thoughts.plan)
            ):
                print_attribute("PLAN", "", title_color=Fore.YELLOW)
                # If it's a list, join it into a string
                if isinstance(assistant_thoughts_plan, list):
                    assistant_thoughts_plan = "\n".join(assistant_thoughts_plan)
                elif isinstance(assistant_thoughts_plan, dict):
                    assistant_thoughts_plan = str(assistant_thoughts_plan)

                # Split the input_string using the newline character and dashes
                lines = assistant_thoughts_plan.split("\n")
                for line in lines:
                    line = line.lstrip("- ")
                    self.logger.info(
                        line.strip(), extra={"title": "- ", "title_color": Fore.GREEN}
                    )
            print_attribute(
                "CRITICISM",
                self._remove_ansi_escape(thoughts.self_criticism),
                title_color=Fore.YELLOW,
            )