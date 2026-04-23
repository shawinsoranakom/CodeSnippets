def fetch_one(self, instance):
        instance.refresh_from_db(fields=[self.field.attname])