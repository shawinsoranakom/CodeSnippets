def get_extra_restriction(self, alias, remote_alias):
        field = self.remote_field.model._meta.get_field(self.content_type_field_name)
        contenttype_pk = self.get_content_type().pk
        lookup = field.get_lookup("exact")(field.get_col(remote_alias), contenttype_pk)
        return WhereNode([lookup], connector=AND)