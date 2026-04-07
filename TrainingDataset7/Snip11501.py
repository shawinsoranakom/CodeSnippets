def fetch_many(self, instances):
        is_cached = self.is_cached
        missing_instances = [i for i in instances if not is_cached(i)]
        prefetch_related_objects(missing_instances, self.field.name)