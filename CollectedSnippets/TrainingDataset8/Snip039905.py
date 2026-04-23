def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._prev_environ)