def print_prompt_summary(prompt_messages: List[ChatCompletionMessageParam], truncate: bool = True):
    summary = format_prompt_summary(prompt_messages, truncate)
    lines = summary.split('\n')

    # Find the maximum line length, with a minimum of 20
    # If truncating, max is 80, otherwise allow up to 120 for full content
    max_allowed = 80 if truncate else 120
    max_length = max(len(line) for line in lines) if lines else 20
    max_length = max(20, min(max_allowed, max_length))

    # Ensure title fits
    title = "PROMPT SUMMARY"
    max_length = max(max_length, len(title) + 4)

    print("┌─" + "─" * max_length + "─┐")
    title_padding = (max_length - len(title)) // 2
    print(f"│ {' ' * title_padding}{title}{' ' * (max_length - len(title) - title_padding)} │")
    print("├─" + "─" * max_length + "─┤")

    for line in lines:
        if len(line) <= max_length:
            print(f"│ {line:<{max_length}} │")
        else:
            # Wrap long lines
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= max_length:
                    current_line += (" " + word) if current_line else word
                else:
                    if current_line:
                        print(f"│ {current_line:<{max_length}} │")
                    current_line = word
            if current_line:
                print(f"│ {current_line:<{max_length}} │")

    print("└─" + "─" * max_length + "─┘")
    print()