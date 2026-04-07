def find_migration(self, loader, app_label, name):
        try:
            return loader.get_migration_by_prefix(app_label, name)
        except AmbiguityError:
            raise CommandError(
                "More than one migration matches '%s' in app '%s'. Please be "
                "more specific." % (name, app_label)
            )
        except KeyError:
            raise CommandError(
                "Cannot find a migration matching '%s' from app '%s'."
                % (name, app_label)
            )