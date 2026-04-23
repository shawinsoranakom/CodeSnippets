def run(self) -> SelectionResult:
        """Run the interactive selector."""
        # Print header with Rich
        header = Text()
        header.append(f"{self.title}", style="bold cyan")
        if self.subtitle:
            header.append(f"\n{self.subtitle}", style="dim")

        self.console.print()
        self.console.print(Panel(header, border_style="cyan", padding=(0, 1)))
        self.console.print()

        num_lines = self._total_options + 2  # options + blank + help

        # Initial render
        output = self._render()
        print(output, flush=True)

        while True:
            ch = _getch()

            # Handle context input mode (Tab on regular option)
            if self.adding_context:
                if ch == "\r" or ch == "\n":  # Enter - confirm with context
                    self._clear_lines(num_lines)
                    choice = self.choices[self.selected_index]
                    context = (
                        self.context_buffer if self.context_buffer.strip() else None
                    )
                    if context:
                        result_text = (
                            f"  \033[1;32m✓\033[0m \033[32m{choice}\033[0m "
                            f"\033[33m+ {context}\033[0m"
                        )
                    else:
                        result_text = f"  \033[1;32m✓\033[0m \033[32m{choice}\033[0m"
                    print(result_text)
                    print()
                    return SelectionResult(
                        choice=choice, index=self.selected_index, feedback=context
                    )
                elif ch == "\x1b":  # Escape - cancel context
                    self.adding_context = False
                    self.context_buffer = ""
                elif ch == "\x7f" or ch == "\x08":  # Backspace
                    self.context_buffer = self.context_buffer[:-1]
                elif ch == "\x03":  # Ctrl+C
                    raise KeyboardInterrupt()
                elif ch.isprintable():
                    self.context_buffer += ch

            # Navigation (when not in context mode)
            elif ch == "\x1b[A":  # Up arrow
                self.selected_index = (self.selected_index - 1) % self._total_options
            elif ch == "\x1b[B":  # Down arrow
                self.selected_index = (self.selected_index + 1) % self._total_options
            elif ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt()

            # Tab - add context to current selection (not on feedback option)
            elif ch == "\t" and not self._on_feedback_option:
                self.adding_context = True
                self.context_buffer = ""

            # Enter key
            elif ch == "\r" or ch == "\n":
                if self._on_feedback_option and self.feedback_buffer.strip():
                    # Submit feedback
                    self._clear_lines(num_lines)
                    fb = self.feedback_buffer
                    result_text = f"  \033[1;32m✓\033[0m \033[33mFeedback: {fb}\033[0m"
                    print(result_text)
                    print()
                    return SelectionResult(
                        choice="feedback",
                        index=self.FEEDBACK_INDEX,
                        feedback=self.feedback_buffer,
                    )
                elif not self._on_feedback_option:
                    # Select regular option
                    self._clear_lines(num_lines)
                    choice = self.choices[self.selected_index]
                    result_text = f"  \033[1;32m✓\033[0m \033[32m{choice}\033[0m"
                    print(result_text)
                    print()
                    return SelectionResult(
                        choice=choice,
                        index=self.selected_index,
                        feedback=None,
                    )
                # On feedback option with no text - do nothing (need to type something)

            # Escape key
            elif ch == "\x1b":
                if self._on_feedback_option and self.feedback_buffer:
                    # Clear feedback buffer
                    self.feedback_buffer = ""
                else:
                    # Exit with first option
                    self._clear_lines(num_lines)
                    choice = self.choices[0]
                    result_text = f"  \033[1;32m✓\033[0m \033[32m{choice}\033[0m"
                    print(result_text)
                    print()
                    return SelectionResult(choice=choice, index=0, feedback=None)

            # Quick select numbers
            elif ch in "12345" and not self._on_feedback_option:
                idx = int(ch) - 1
                if idx < len(self.choices):
                    self._clear_lines(num_lines)
                    choice = self.choices[idx]
                    result_text = f"  \033[1;32m✓\033[0m \033[32m{choice}\033[0m"
                    print(result_text)
                    print()
                    return SelectionResult(choice=choice, index=idx, feedback=None)
                elif idx == len(self.choices) and self.show_feedback_option:
                    # Jump to feedback option
                    self.selected_index = idx

            # Backspace (when on feedback option)
            elif (ch == "\x7f" or ch == "\x08") and self._on_feedback_option:
                self.feedback_buffer = self.feedback_buffer[:-1]

            # Printable character - if on feedback option, type directly
            elif ch.isprintable():
                if self._on_feedback_option:
                    self.feedback_buffer += ch

            # Re-render
            self._clear_lines(num_lines)
            output = self._render()
            print(output, flush=True)