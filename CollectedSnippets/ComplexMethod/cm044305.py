def format_description(description: str) -> str:
            """Format description in docstrings with proper indentation for provider choices."""
            # Base indent for description content (called with create_indent(3) prefix)
            base_indent = create_indent(3)  # 12 spaces

            # Extract "Choices for provider: ..." into a dict keyed by provider
            provider_choices: dict[str, str] = {}
            main_description = description
            multi_items_text = ""

            if "\nChoices for " in description:
                choices_idx = description.index("\nChoices for ")
                main_description = description[:choices_idx]
                choices_text = description[choices_idx:]

                # Parse each "Choices for provider: values" line
                # Handle multi-line choices where continuation lines don't have "Choices for" prefix
                current_provider = None
                current_choices = []

                for ln in choices_text.strip().split("\n"):
                    line = ln.strip()

                    # Check if this is the "Multiple comma separated" line
                    if line.startswith("Multiple comma separated items allowed"):
                        # Save current provider's choices first
                        if current_provider and current_choices:
                            provider_choices[current_provider] = " ".join(
                                current_choices
                            )
                            current_provider = None
                            current_choices = []
                        multi_items_text = line
                        continue

                    if line.startswith("Choices for "):
                        # Save previous provider's choices if any
                        if current_provider and current_choices:
                            provider_choices[current_provider] = " ".join(
                                current_choices
                            )

                        # Extract provider name and choices
                        rest = line[len("Choices for ") :]
                        if ": " in rest:
                            prov, choices = rest.split(": ", 1)
                            current_provider = prov.strip()
                            current_choices = [choices.strip()]
                    elif current_provider and line:
                        # This is a continuation line for the current provider's choices
                        current_choices.append(line)

                # Save the last provider's choices
                if current_provider and current_choices:
                    provider_choices[current_provider] = " ".join(current_choices)

            # Extract multiple items text from main_description if not already found
            if not multi_items_text:
                multi_pattern = (
                    r"\nMultiple comma separated items allowed for provider\(s\): [^.]+"
                )
                multi_match = re.search(multi_pattern, main_description)
                if multi_match:
                    multi_items_text = multi_match.group().strip()
                    main_description = re.sub(multi_pattern, "", main_description)

            # Handle semicolon-separated provider descriptions
            if ";" in main_description and "(provider:" in main_description:
                parts = main_description.split(";")
                provider_sections = []

                # Extract provider tag pattern
                provider_pattern = re.compile(r"\s*\(provider:\s*([^)]+)\)")

                for part in parts:
                    p = part.strip()
                    match = provider_pattern.search(p)
                    if match:
                        provider_name = match.group(1).strip()
                        content = provider_pattern.sub("", p).strip()
                        provider_sections.append((provider_name, content))
                    elif p:
                        provider_sections.append((None, p))

                if provider_sections:
                    # Find common base description
                    provider_contents = [
                        (name, content)
                        for name, content in provider_sections
                        if name is not None
                    ]
                    base_description = ""

                    if len(provider_contents) >= 2:
                        first_sentences = []
                        for _, content in provider_contents:
                            if "." in content:
                                first_sent = content.split(".", 1)[0].strip()
                                first_sentences.append(first_sent)
                            else:
                                first_sentences.append(content)

                        if first_sentences and all(
                            s == first_sentences[0] for s in first_sentences
                        ):
                            base_description = first_sentences[0] + "."

                    # Check for base description without provider tag
                    base_parts = [
                        content
                        for name, content in provider_sections
                        if name is None and "Choices" not in content
                    ]
                    if base_parts and not base_description:
                        base_description = base_parts[0]

                    # Build formatted output
                    formatted_lines = []

                    if base_description:
                        formatted_lines.append(base_description)
                        formatted_lines.append("")

                    for provider_name, content in provider_sections:
                        if provider_name and content:
                            if base_description:
                                base_clean = base_description.rstrip(".")
                                if content.startswith(base_clean):
                                    content = content[len(base_clean) :].strip()  # noqa
                                    if content.startswith("."):
                                        content = content[1:].strip()  # noqa

                            if not content:
                                continue

                            formatted_lines.append(f"(provider: {provider_name})")
                            for line in content.split("\n"):
                                new_line = line.strip()
                                if new_line:
                                    formatted_lines.append(f"    {new_line}")

                            # Add choices for this provider inside its section
                            if provider_name in provider_choices:
                                formatted_lines.append(
                                    f"    Choices: {provider_choices[provider_name]}"
                                )

                            formatted_lines.append("")

                    while formatted_lines and formatted_lines[-1] == "":
                        formatted_lines.pop()

                    # Join lines
                    if formatted_lines:
                        result = formatted_lines[0]
                        for line in formatted_lines[1:]:
                            if line:
                                result += f"\n{base_indent}{line}"
                            else:
                                result += "\n"
                        main_description = result

            # If no provider sections but we have choices, add them at the end
            elif provider_choices:
                for prov, choices in provider_choices.items():
                    main_description += f"\n{base_indent}Choices for {prov}: {choices}"

            # Add multiple items text at the end
            if multi_items_text:
                main_description += f"\n{base_indent}{multi_items_text}"

            return main_description