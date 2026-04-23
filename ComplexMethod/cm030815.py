def test_all_exported_names(self):
        # ensure all dynamically created objects are actualised
        for name in typing.__all__:
            getattr(typing, name)

        actual_all = set(typing.__all__)
        computed_all = {
            k for k, v in vars(typing).items()
            # explicitly exported, not a thing with __module__
            if k in actual_all or (
                # avoid private names
                not k.startswith('_') and
                # there's a few types and metaclasses that aren't exported
                not k.endswith(('Meta', '_contra', '_co')) and
                not k.upper() == k and
                k not in {"ByteString"} and
                # but export all other things that have __module__ == 'typing'
                getattr(v, '__module__', None) == typing.__name__
            )
        }
        self.assertSetEqual(computed_all, actual_all)