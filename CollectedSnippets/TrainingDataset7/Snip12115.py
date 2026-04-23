def __init__(self, relation_name, *, condition=Q()):
        if not relation_name:
            raise ValueError("relation_name cannot be empty.")
        self.relation_name = relation_name
        self.alias = None
        if not isinstance(condition, Q):
            raise ValueError("condition argument must be a Q() instance.")
        # .condition and .resolved_condition have to be stored independently
        # as the former must remain unchanged for Join.__eq__ to remain stable
        # and reusable even once their .filtered_relation are resolved.
        self.condition = condition
        self.resolved_condition = None