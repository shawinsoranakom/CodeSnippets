def handle(self, *tablenames, **options):
        db = options["database"]
        self.verbosity = options["verbosity"]
        dry_run = options["dry_run"]
        if tablenames:
            # Legacy behavior, tablename specified as argument
            for tablename in tablenames:
                self.create_table(db, tablename, dry_run)
        else:
            for cache_alias in settings.CACHES:
                cache = caches[cache_alias]
                if isinstance(cache, BaseDatabaseCache):
                    self.create_table(db, cache._table, dry_run)