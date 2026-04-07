def fetch_many(self, instances):
        attname = self.field.attname
        db = instances[0]._state.db
        value_by_pk = (
            self.field.model._base_manager.using(db)
            .values_list(attname)
            .in_bulk({i.pk for i in instances})
        )
        for instance in instances:
            setattr(instance, attname, value_by_pk[instance.pk])