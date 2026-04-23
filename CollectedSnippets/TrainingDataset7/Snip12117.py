def clone(self):
        clone = FilteredRelation(self.relation_name, condition=self.condition)
        clone.alias = self.alias
        if (resolved_condition := self.resolved_condition) is not None:
            clone.resolved_condition = resolved_condition.clone()
        return clone