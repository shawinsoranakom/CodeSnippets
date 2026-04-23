def print_help(self):
        """Print help."""
        mt = MenuText("")
        mt.add_info("\nConfigure CLI")
        mt.add_menu(
            "settings",
            description="enable and disable feature flags, preferences and settings",
        )
        mt.add_raw("\n")
        mt.add_info("Record and execute your own .openbb routine scripts")
        mt.add_cmd("record", description="start recording current session")
        mt.add_cmd(
            "stop", description="stop session recording and convert to .openbb routine"
        )
        mt.add_cmd(
            "exe",
            description="execute .openbb routine scripts (use exe --example for an example)",
        )
        mt.add_raw("\n")
        mt.add_info("Retrieve data from different asset classes and providers")

        for router, value in PLATFORM_ROUTERS.items():
            if router in NON_DATA_ROUTERS or router in DATA_PROCESSING_ROUTERS:
                continue
            if value == "menu":
                menu_description = (
                    obb.reference["routers"].get(f"{self.PATH}{router}", {}).get("description")  # type: ignore
                ) or ""
                mt.add_menu(
                    name=router,
                    description=menu_description.split(".")[0].lower(),
                )
            else:
                mt.add_cmd(router)

        if any(router in PLATFORM_ROUTERS for router in DATA_PROCESSING_ROUTERS):
            mt.add_info("\nAnalyze and process previously obtained data")

            for router, value in PLATFORM_ROUTERS.items():
                if router not in DATA_PROCESSING_ROUTERS:
                    continue
                if value == "menu":
                    menu_description = (
                        obb.reference["routers"].get(f"{self.PATH}{router}", {}).get("description")  # type: ignore
                    ) or ""
                    mt.add_menu(
                        name=router,
                        description=menu_description.split(".")[0].lower(),
                    )
                else:
                    mt.add_cmd(router)

        mt.add_raw("\n")
        mt.add_cmd("results")
        if session.obbject_registry.obbjects:
            mt.add_info("\nCached Results")
            for key, value in list(session.obbject_registry.all.items())[  # type: ignore
                : session.settings.N_TO_DISPLAY_OBBJECT_REGISTRY
            ]:
                mt.add_raw(
                    f"[yellow]OBB{key}[/yellow]: {value['command']}",  # type: ignore[index]
                    left_spacing=True,
                )

        session.console.print(text=mt.menu_text, menu="Home")
        self.update_runtime_choices()