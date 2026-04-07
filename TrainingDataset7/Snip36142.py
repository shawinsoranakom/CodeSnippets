def assertPolicyEqual(self, a, b):
        parts_a = sorted(a.split("; ")) if a is not None else None
        parts_b = sorted(b.split("; ")) if b is not None else None
        self.assertEqual(parts_a, parts_b, f"Policies not equal: {a!r} != {b!r}")