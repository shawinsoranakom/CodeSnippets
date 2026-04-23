def migration_qs(self):
        return self.Migration.objects.using(self.connection.alias)