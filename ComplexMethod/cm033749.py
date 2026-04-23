def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value = state.read()
        choices = self.get_choices(value)

        if state.mode == ParserMode.PARSE or state.incomplete:
            if self.conditions & MatchConditions.CHOICE and state.match(value, choices):
                return value

            if self.conditions & MatchConditions.ANY and value:
                return value

            if self.conditions & MatchConditions.NOTHING and not value and state.current_boundary and not state.current_boundary.match:
                return value

            if state.mode == ParserMode.PARSE:
                if choices:
                    raise ParserError(f'"{value}" not in: {", ".join(choices)}')

                raise self.no_choices_available(value)

            raise CompletionUnavailable()

        matches = [choice for choice in choices if choice.startswith(value)]

        if not matches:
            raise self.no_completion_match(value)

        continuation = state.current_boundary.delimiters if state.current_boundary and state.current_boundary.required else ''

        raise CompletionSuccess(
            list_mode=state.mode == ParserMode.LIST,
            consumed=state.consumed,
            continuation=continuation,
            matches=matches,
        )