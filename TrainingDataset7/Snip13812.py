def take_screenshot(self, name):
        if not self.screenshots:
            return
        test = getattr(self, self._testMethodName)
        filename = f"{test._screenshot_name}--{name}--{test._screenshot_case}.png"
        path = Path.cwd() / "screenshots" / filename
        path.parent.mkdir(exist_ok=True, parents=True)
        self.selenium.save_screenshot(path)