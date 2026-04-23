def print_help(self):
        """Print help."""
        mt = MenuText(self.PATH)

        if self.CHOICES_MENUS:
            for menu in self.CHOICES_MENUS:
                description = self._get_menu_description(menu)
                mt.add_menu(name=menu, description=description)

            if self.CHOICES_COMMANDS:
                mt.add_raw("\n")

        if self.CHOICES_COMMANDS:
            for command in self.CHOICES_COMMANDS:
                command_description = self._get_command_description(command)
                mt.add_cmd(
                    name=command.replace(f"{self._name}_", ""),
                    description=command_description,
                )

        if session.obbject_registry.obbjects:
            mt.add_info("\nCached Results")
            for key, value in list(session.obbject_registry.all.items())[
                : session.settings.N_TO_DISPLAY_OBBJECT_REGISTRY
            ]:
                mt.add_raw(
                    f"[yellow]OBB{key}[/yellow]: {value['command']}",
                    left_spacing=True,
                )

        session.console.print(text=mt.menu_text, menu=self.PATH)

        if mt.warnings:
            session.console.print("")
            for w in mt.warnings:
                w_str = str(w).replace("{", "").replace("}", "").replace("'", "")
                session.console.print(f"[yellow]{w_str}[/yellow]")
            session.console.print("")