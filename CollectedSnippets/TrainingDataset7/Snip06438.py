def _is_matching_generic_foreign_key(self, field):
        """
        Return True if field is a GenericForeignKey whose content type and
        object id fields correspond to the equivalent attributes on this
        GenericRelation.
        """
        return (
            isinstance(field, GenericForeignKey)
            and field.ct_field == self.content_type_field_name
            and field.fk_field == self.object_id_field_name
        )