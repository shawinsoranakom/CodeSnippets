def _testCode(self, code: str, expected_count: int) -> None:
        tree = magic.add_magic(code, "./")
        count = 0
        for node in ast.walk(tree):
            # count the nodes where a substitution has been made, i.e.
            # look for 'calls' to a '__streamlitmagic__' function
            if type(node) is ast.Call and magic.MAGIC_MODULE_NAME in ast.dump(
                node.func
            ):
                count += 1
        self.assertEqual(
            expected_count,
            count,
            f"There must be exactly {expected_count} {magic.MAGIC_MODULE_NAME} nodes, but found {count}",
        )