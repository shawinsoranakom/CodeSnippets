def _render_settings(self) -> None:
        """Render settings for the current category."""
        if not self.categories:
            self.console.print("  [dim]No settings available[/dim]")
            return

        category = self.categories[self.current_tab]
        settings = category.get_settings(self.all_settings)

        if not settings:
            self.console.print(f"  [dim]No settings in {category.name}[/dim]")
            return

        for i, setting in enumerate(settings):
            is_selected = i == self.selected_index
            value = self.values.get(setting.env_var, "")
            display_value = setting.get_display_value(value or None)

            # Determine if value has changed from original
            changed = value != self.original_values.get(setting.env_var, "")

            line = Text()
            if is_selected:
                line.append("  ❯ ", style="bold green")
                line.append(setting.env_var, style="bold green")
            else:
                line.append("    ", style="dim")
                line.append(setting.env_var, style="dim")

            # Pad to align values
            padding = 30 - len(setting.env_var)
            line.append(" " * max(padding, 1))

            # Value
            if display_value == "[not set]":
                line.append(display_value, style="dim italic")
            elif changed:
                line.append(display_value, style="yellow")
            else:
                line.append(display_value, style="white")

            self.console.print(line)