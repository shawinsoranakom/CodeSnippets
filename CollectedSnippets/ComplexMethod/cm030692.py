def assertNamespaceMatches(self, result_ns, expected_ns):
        """Check two namespaces match.

           Ignores any unspecified interpreter created names
        """
        # Avoid side effects
        result_ns = result_ns.copy()
        expected_ns = expected_ns.copy()
        # Impls are permitted to add extra names, so filter them out
        for k in list(result_ns):
            if k.startswith("__") and k.endswith("__"):
                if k not in expected_ns:
                    result_ns.pop(k)
                if k not in expected_ns["nested"]:
                    result_ns["nested"].pop(k)
        # Spec equality includes the loader, so we take the spec out of the
        # result namespace and check that separately
        result_spec = result_ns.pop("__spec__")
        expected_spec = expected_ns.pop("__spec__")
        if expected_spec is None:
            self.assertIsNone(result_spec)
        else:
            # If an expected loader is set, we just check we got the right
            # type, rather than checking for full equality
            if expected_spec.loader is not None:
                self.assertEqual(type(result_spec.loader),
                                 type(expected_spec.loader))
            for attr in self.CHECKED_SPEC_ATTRIBUTES:
                k = "__spec__." + attr
                actual = (k, getattr(result_spec, attr))
                expected = (k, getattr(expected_spec, attr))
                self.assertEqual(actual, expected)
        # For the rest, we still don't use direct dict comparison on the
        # namespace, as the diffs are too hard to debug if anything breaks
        self.assertEqual(set(result_ns), set(expected_ns))
        for k in result_ns:
            actual = (k, result_ns[k])
            expected = (k, expected_ns[k])
            self.assertEqual(actual, expected)