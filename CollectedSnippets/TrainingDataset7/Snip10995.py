def fetch(self, fetcher, instance):
        klass = instance.__class__.__qualname__
        field_name = fetcher.field.name
        raise FieldFetchBlocked(f"Fetching of {klass}.{field_name} blocked.") from None