def _locate_plugins(debug: bool | None = False) -> None:
        """Locate all the plugins in the plugins folder."""
        path = (
            Path(sys.executable).parent
            if hasattr(sys, "frozen")
            else CHARTING_INSTALL_PATH
        )
        if debug:
            warnings.warn(f"[bold green]Loading plugins from {path}[/]")
            warnings.warn("[bold green]Plugins found:[/]")

        for plugin in Path(__file__).parent.glob("plugins/*_plugin.py"):
            python_path = plugin.relative_to(path).with_suffix("")

            if debug:
                warnings.warn(f"    [bold red]{plugin.name}[/]")
                warnings.warn(f"        [bold yellow]{python_path}[/]")
                warnings.warn(f"        [bold bright_cyan]{__package__}[/]")
                warnings.warn(f"        [bold magenta]{python_path.parts}[/]")
                warnings.warn(
                    f"        [bold bright_magenta]{'.'.join(python_path.parts)}[/]"
                )

            module = importlib.import_module(
                ".".join(python_path.parts), package=__package__
            )
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, (PltTA))
                    and obj != PlotlyTA.__class__
                ) and obj not in PlotlyTA.plugins:
                    PlotlyTA.plugins.append(obj)