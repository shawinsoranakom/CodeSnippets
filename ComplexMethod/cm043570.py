def print(self, *args, **kwargs):
        """Print the text to the console."""
        if kwargs and "text" in list(kwargs) and "menu" in list(kwargs):
            if not self._settings.TEST_MODE:
                if self._settings.ENABLE_RICH_PANEL:
                    if self._settings.SHOW_VERSION:
                        version = self._settings.VERSION
                        version = f"[param]OpenBB Platform CLI v{version}[/param] (https://openbb.co)"
                    else:
                        version = (
                            "[param]OpenBB Platform CLI[/param] (https://openbb.co)"
                        )
                    self._console.print(
                        panel.Panel(
                            "\n" + kwargs["text"],
                            title=kwargs["menu"],
                            subtitle_align="right",
                            subtitle=version,
                        )
                    )

                else:
                    self._console.print(kwargs["text"])
            else:
                print(self._filter_rich_tags(kwargs["text"]))  # noqa: T201
        elif not self._settings.TEST_MODE:
            self._console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)