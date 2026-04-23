def test_code_locator(self):
        locator = github_links.CodeLocator.from_code("""
from a import b, c
from .d import e, f as g

def h():
    pass

class I:
    def j(self):
        pass""")

        self.assertEqual(locator.node_line_numbers, {"h": 5, "I": 8, "I.j": 9})
        self.assertEqual(locator.import_locations, {"b": "a", "c": "a", "e": ".d"})