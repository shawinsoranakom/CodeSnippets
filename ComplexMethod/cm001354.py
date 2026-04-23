def _edit_current_setting(self) -> None:
        """Edit the currently selected setting."""
        if not self.categories:
            return

        category = self.categories[self.current_tab]
        settings = category.get_settings(self.all_settings)

        if not settings or self.selected_index >= len(settings):
            return

        setting = settings[self.selected_index]
        current_value = self.values.get(setting.env_var, "")

        # Clear screen for edit mode
        self.console.clear()
        self.console.print()

        new_value: Any = None

        if setting.field_type == "secret":
            masked = setting.get_display_value(current_value or None)
            new_value = prompt_secret_input(
                self.console,
                label=setting.env_var,
                description=setting.description,
                current_masked=masked if masked != "[not set]" else "",
                env_var=setting.env_var,
            )
            # Keep current value if empty input
            if not new_value and current_value:
                return

        elif setting.field_type == "choice":
            default_idx = 0
            if current_value and current_value in setting.choices:
                default_idx = setting.choices.index(current_value)
            new_value = prompt_selection(
                label=setting.env_var,
                choices=setting.choices,
                description=setting.description,
                default_index=default_idx,
                env_var=setting.env_var,
            )

        elif setting.field_type == "bool":
            current_bool = (
                current_value.lower() in ("true", "1", "yes")
                if current_value
                else False
            )
            result = prompt_boolean(
                self.console,
                label=setting.env_var,
                description=setting.description,
                default=current_bool,
                env_var=setting.env_var,
            )
            new_value = "true" if result else "false"

        elif setting.field_type == "int":
            current_int = (
                int(current_value)
                if current_value and current_value.isdigit()
                else None
            )
            result = prompt_numeric(
                self.console,
                label=setting.env_var,
                description=setting.description,
                default=current_int,
                env_var=setting.env_var,
            )
            new_value = str(result) if result is not None else ""

        elif setting.field_type == "float":
            try:
                current_float = float(current_value) if current_value else None
            except ValueError:
                current_float = None
            result = prompt_float(
                self.console,
                label=setting.env_var,
                description=setting.description,
                default=current_float,
                env_var=setting.env_var,
            )
            new_value = str(result) if result is not None else ""

        else:  # str
            new_value = prompt_text_input(
                self.console,
                label=setting.env_var,
                description=setting.description,
                default=current_value,
                env_var=setting.env_var,
            )

        # Validate the new value
        if new_value:
            is_valid, error = validate_setting(setting.env_var, new_value)
            if not is_valid:
                self.console.print(f"\n[red]Validation error: {error}[/red]")
                self.console.print("[dim]Press any key to continue...[/dim]")
                _getch()
                return
            elif error:  # Warning
                self.console.print(f"\n[yellow]{error}[/yellow]")

        # Update value
        if new_value != current_value:
            self.values[setting.env_var] = new_value
            self.has_unsaved_changes = True