def _is_end_tool_calls(self, current_text: str) -> bool:
        if self.tool_call_end_token not in current_text:
            return False

        end_token_positions = []
        search_start = 0
        while True:
            pos = current_text.find(self.tool_call_end_token, search_start)
            if pos == -1:
                break
            end_token_positions.append(pos)
            search_start = pos + 1

        think_regions = []
        for match in re.finditer(
            self.thinking_tag_pattern, current_text, flags=re.DOTALL
        ):
            think_regions.append((match.start(), match.end()))

        for pos in end_token_positions:
            in_think = any(
                pos >= t_start and pos < t_end for t_start, t_end in think_regions
            )
            if not in_think:
                return True

        return False