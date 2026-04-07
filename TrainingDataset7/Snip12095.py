def referenced_base_fields(self):
        """
        Retrieve all base fields referenced directly or through F expressions
        excluding any fields referenced through joins.
        """
        # Avoid circular imports.
        from django.db.models.sql import query

        return {
            child.split(LOOKUP_SEP, 1)[0] for child in query.get_children_from_q(self)
        }