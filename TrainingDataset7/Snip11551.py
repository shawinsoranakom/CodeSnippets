def constrained_target(self):
            # If the through relation's target field's foreign integrity is
            # enforced, the query can be performed solely against the through
            # table as the INNER JOIN'ing against target table is unnecessary.
            if not self.target_field.db_constraint:
                return None
            db = router.db_for_read(self.through, instance=self.instance)
            if not connections[db].features.supports_foreign_keys:
                return None
            hints = {"instance": self.instance}
            manager = self.through._base_manager.db_manager(db, hints=hints)
            filters = {self.source_field_name: self.related_val[0]}
            # Nullable target rows must be excluded as well as they would have
            # been filtered out from an INNER JOIN.
            if self.target_field.null:
                filters["%s__isnull" % self.target_field_name] = False
            return manager.filter(**filters)