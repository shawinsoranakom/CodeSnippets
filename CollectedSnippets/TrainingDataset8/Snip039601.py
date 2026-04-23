def test_import(self):
        """Test code that imports module."""

        def f():
            import numpy

            return numpy

        def g():
            import pandas

            return pandas

        def n():
            import foobar

            return foobar

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertNotEqual(get_hash(f), get_hash(n))