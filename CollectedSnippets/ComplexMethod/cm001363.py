def _render(self) -> str:
        """Render the selector as a plain string."""
        lines = []

        # Regular choices
        for i, choice in enumerate(self.choices):
            if i == self.selected_index:
                if self.adding_context:
                    # Show choice + context being typed
                    ctx = self.context_buffer
                    lines.append(
                        f"  \033[1;32m❯ {choice}\033[0m \033[33m+ {ctx}\033[5m█\033[0m"
                    )
                else:
                    lines.append(f"  \033[1;32m❯ {choice}\033[0m")
            else:
                lines.append(f"    \033[2m{choice}\033[0m")

        # Feedback option - inline text input
        if self.show_feedback_option:
            feedback_idx = len(self.choices)
            if self.selected_index == feedback_idx:
                if self.feedback_buffer:
                    # Show typed text with cursor
                    lines.append(f"  \033[1;33m❯ {self.feedback_buffer}\033[5m█\033[0m")
                else:
                    # Show placeholder as shadow text with cursor
                    ph = self.feedback_placeholder
                    lines.append(f"  \033[1;33m❯ \033[2;33m{ph}\033[0;5;33m█\033[0m")
            else:
                if self.feedback_buffer:
                    # Show typed text (not selected)
                    lines.append(f"    \033[2;33m{self.feedback_buffer}\033[0m")
                else:
                    # Show placeholder (not selected)
                    lines.append(f"    \033[2m{self.feedback_placeholder}\033[0m")

        # Help text
        lines.append("")
        # ANSI: \033[2m=dim, \033[1;36m=bold cyan, \033[0;2m=reset+dim, \033[0m=reset
        if self.adding_context:
            lines.append(
                "  \033[2mType context, \033[1;36mEnter\033[0;2m confirm, "
                "\033[1;36mEsc\033[0;2m cancel\033[0m"
            )
        elif self._on_feedback_option:
            lines.append(
                "  \033[1;36m↑↓\033[0;2m move  \033[1;36mEnter\033[0;2m send  "
                "\033[1;36mEsc\033[0;2m clear  \033[2mjust start typing...\033[0m"
            )
        else:
            lines.append(
                "  \033[1;36m↑↓\033[0;2m move  \033[1;36mEnter\033[0;2m select  "
                "\033[1;36mTab\033[0;2m +context  \033[1;36m1-5\033[0;2m quick\033[0m"
            )

        return "\n".join(lines)