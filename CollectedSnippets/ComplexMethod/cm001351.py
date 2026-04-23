def print_assistant_thoughts(
    ai_name: str,
    thoughts: str | ModelWithSummary | AssistantThoughts,
    speak_mode: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    thoughts_text = remove_ansi_escape(
        thoughts.reasoning
        if isinstance(thoughts, AssistantThoughts)
        else thoughts.summary() if isinstance(thoughts, ModelWithSummary) else thoughts
    )
    print_attribute(
        f"{ai_name.upper()} THOUGHTS", thoughts_text, title_color=Fore.YELLOW
    )

    if isinstance(thoughts, AssistantThoughts):
        if assistant_thoughts_plan := remove_ansi_escape(
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
                logger.info(
                    line.strip(), extra={"title": "- ", "title_color": Fore.GREEN}
                )
        print_attribute(
            "CRITICISM",
            remove_ansi_escape(thoughts.self_criticism),
            title_color=Fore.YELLOW,
        )