def test_hash_no_args(self):
        # Test dataclasses with no hash= argument.  This exists to
        #  make sure that if the @dataclass parameter name is changed
        #  or the non-default hashing behavior changes, the default
        #  hashability keeps working the same way.

        class Base:
            def __hash__(self):
                return 301

        # If frozen or eq is None, then use the default value (do not
        #  specify any value in the decorator).
        for frozen, eq,    base,   expected       in [
            (None,  None,  object, 'unhashable'),
            (None,  None,  Base,   'unhashable'),
            (None,  False, object, 'object'),
            (None,  False, Base,   'base'),
            (None,  True,  object, 'unhashable'),
            (None,  True,  Base,   'unhashable'),
            (False, None,  object, 'unhashable'),
            (False, None,  Base,   'unhashable'),
            (False, False, object, 'object'),
            (False, False, Base,   'base'),
            (False, True,  object, 'unhashable'),
            (False, True,  Base,   'unhashable'),
            (True,  None,  object, 'tuple'),
            (True,  None,  Base,   'tuple'),
            (True,  False, object, 'object'),
            (True,  False, Base,   'base'),
            (True,  True,  object, 'tuple'),
            (True,  True,  Base,   'tuple'),
            ]:

            with self.subTest(frozen=frozen, eq=eq, base=base, expected=expected):
                # First, create the class.
                if frozen is None and eq is None:
                    @dataclass
                    class C(base):
                        i: int
                elif frozen is None:
                    @dataclass(eq=eq)
                    class C(base):
                        i: int
                elif eq is None:
                    @dataclass(frozen=frozen)
                    class C(base):
                        i: int
                else:
                    @dataclass(frozen=frozen, eq=eq)
                    class C(base):
                        i: int

                # Now, make sure it hashes as expected.
                if expected == 'unhashable':
                    c = C(10)
                    with self.assertRaisesRegex(TypeError, 'unhashable type'):
                        hash(c)

                elif expected == 'base':
                    self.assertEqual(hash(C(10)), 301)

                elif expected == 'object':
                    # I'm not sure what test to use here.  object's
                    #  hash isn't based on id(), so calling hash()
                    #  won't tell us much.  So, just check the
                    #  function used is object's.
                    self.assertIs(C.__hash__, object.__hash__)

                elif expected == 'tuple':
                    self.assertEqual(hash(C(42)), hash((42,)))

                else:
                    assert False, f'unknown value for expected={expected!r}'