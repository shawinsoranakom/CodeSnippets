async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        # List of supported programming languages with mapped aliases
        language_aliases = {
            "html": ["html", "htm"],
            "css": ["css"],
            "javascript": ["javascript", "js"],
            "python": ["python", "py"],
            "sql": ["sql"],
            "java": ["java"],
            "cpp": ["cpp", "c++"],
            "csharp": ["csharp", "c#", "cs"],
            "json_code": ["json"],
            "bash": ["bash", "shell", "sh"],
            "php": ["php"],
            "ruby": ["ruby", "rb"],
            "yaml": ["yaml", "yml"],
            "markdown": ["markdown", "md"],
            "typescript": ["typescript", "ts"],
            "xml": ["xml"],
        }

        # Extract code for each language
        for canonical_name, aliases in language_aliases.items():
            code = ""
            # Try each alias for the language
            for alias in aliases:
                code_for_alias = self.extract_code(input_data.text, alias)
                if code_for_alias:
                    code = code + "\n\n" + code_for_alias if code else code_for_alias

            if code:  # Only yield if there's actual code content
                yield canonical_name, code

        # Remove all code blocks from the text to get remaining text
        pattern = (
            r"```(?:"
            + "|".join(
                re.escape(alias)
                for aliases in language_aliases.values()
                for alias in aliases
            )
            + r")[ \t]*\n[\s\S]*?```"
        )

        remaining_text = re.sub(pattern, "", input_data.text).strip()
        remaining_text = re.sub(r"\n\s*\n", "\n", remaining_text)

        if remaining_text:  # Only yield if there's remaining text
            yield "remaining_text", remaining_text