def _print_rich_exception(e: BaseException):
    from rich import box, panel

    # Monkey patch the panel to use our custom box style
    class ConfigurablePanel(panel.Panel):
        def __init__(
            self,
            renderable,
            box=box.Box("────\n    \n────\n    \n────\n────\n    \n────\n"),
            **kwargs,
        ):
            super(ConfigurablePanel, self).__init__(renderable, box, **kwargs)

    from rich import traceback as rich_traceback

    rich_traceback.Panel = ConfigurablePanel  # type: ignore

    # Configure console
    from rich.console import Console

    console = Console(
        color_system="256",
        force_terminal=True,
        width=88,
        no_color=False,
        tab_size=8,
    )

    # Import script_runner here to prevent circular import
    import streamlit.runtime.scriptrunner.script_runner as script_runner

    # Print exception via rich
    console.print(
        rich_traceback.Traceback.from_exception(
            type(e),
            e,
            e.__traceback__,
            width=88,
            show_locals=False,
            max_frames=100,
            word_wrap=False,
            extra_lines=3,
            suppress=[script_runner],  # Ignore script runner
        )
    )