def _patch_check_field_on(self, db):
        return mock.patch.object(connections[db].validation, "check_field")