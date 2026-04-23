def argparsersEqual(self, a: argparse.ArgumentParser, b: argparse.ArgumentParser):
        """
        Small helper to check pseudo-equality of parsed arguments on `ArgumentParser` instances.
        """
        self.assertEqual(len(a._actions), len(b._actions))
        for x, y in zip(a._actions, b._actions):
            xx = {k: v for k, v in vars(x).items() if k != "container"}
            yy = {k: v for k, v in vars(y).items() if k != "container"}

            # Choices with mixed type have custom function as "type"
            # So we need to compare results directly for equality
            if xx.get("choices") and yy.get("choices"):
                for expected_choice in yy["choices"] + xx["choices"]:
                    self.assertEqual(xx["type"](expected_choice), yy["type"](expected_choice))
                del xx["type"], yy["type"]

            self.assertEqual(xx, yy)