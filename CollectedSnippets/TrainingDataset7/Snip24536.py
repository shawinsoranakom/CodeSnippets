def allow_relation(self, obj1, obj2, **hints):
        # ContentType objects are created during a post-migrate signal while
        # performing fixture teardown using the default database alias and
        # don't abide by the database specified by this router.
        return True