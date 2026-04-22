def run(self) -> None:
        try:
            super().run()
        except Exception as e:
            self._unhandled_exception = e