def stop(self) -> None:
        click.secho("  Stopping...", fg="blue")
        self._runtime.stop()