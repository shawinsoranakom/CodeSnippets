def add_filtered_relation(self, filtered_relation, alias):
        if "." in alias:
            raise ValueError(
                "FilteredRelation doesn't support aliases with periods "
                "(got %r)." % alias
            )
        self.check_alias(alias)
        filtered_relation.alias = alias
        relation_lookup_parts, relation_field_parts, _ = self.solve_lookup_type(
            filtered_relation.relation_name
        )
        if relation_lookup_parts:
            raise ValueError(
                "FilteredRelation's relation_name cannot contain lookups "
                "(got %r)." % filtered_relation.relation_name
            )
        for lookup in get_children_from_q(filtered_relation.condition):
            lookup_parts, lookup_field_parts, _ = self.solve_lookup_type(lookup)
            shift = 2 if not lookup_parts else 1
            lookup_field_path = lookup_field_parts[:-shift]
            for idx, lookup_field_part in enumerate(lookup_field_path):
                if len(relation_field_parts) > idx:
                    if relation_field_parts[idx] != lookup_field_part:
                        raise ValueError(
                            "FilteredRelation's condition doesn't support "
                            "relations outside the %r (got %r)."
                            % (filtered_relation.relation_name, lookup)
                        )
            if len(lookup_field_parts) > len(relation_field_parts) + 1:
                raise ValueError(
                    "FilteredRelation's condition doesn't support nested "
                    "relations deeper than the relation_name (got %r for "
                    "%r)." % (lookup, filtered_relation.relation_name)
                )
        filtered_relation = filtered_relation.clone()
        filtered_relation.condition = rename_prefix_from_q(
            filtered_relation.relation_name,
            alias,
            filtered_relation.condition,
        )
        self._filtered_relations[filtered_relation.alias] = filtered_relation