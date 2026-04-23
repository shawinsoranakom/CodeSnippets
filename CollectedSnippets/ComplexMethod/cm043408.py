def formatted_message(self) -> str:
        """Returns the nice text format for terminals"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"{self.type.value.title()} Error [{self.code}]")
        lines.append(f"{'='*60}")
        lines.append(f"Location: Line {self.line}, Column {self.column}")
        lines.append(f"Error: {self.message}")

        if self.source_line:
            marker = " " * (self.column - 1) + "^"
            if self.end_column:
                marker += "~" * (self.end_column - self.column - 1)
            lines.append(f"\nCode:")
            if self.line_before:
                lines.append(f"  {self.line - 1: >3} | {self.line_before}")
            lines.append(f"  {self.line: >3} | {self.source_line}")
            lines.append(f"      | {marker}")
            if self.line_after:
                lines.append(f"  {self.line + 1: >3} | {self.line_after}")

        if self.suggestions:
            lines.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion.message}")
                if suggestion.fix:
                    lines.append(f"     Fix: {suggestion.fix}")

        lines.append("="*60)
        return "\n".join(lines)