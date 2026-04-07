def _update(self, *args, **kwargs):
                FakeQuerySet.called = True
                super()._update(*args, **kwargs)
                return 0