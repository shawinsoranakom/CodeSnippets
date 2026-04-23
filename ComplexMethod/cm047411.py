def get_missing_fields(self):
        """
        return {'field_name': (missing_groups | False, [mandatory_groups, use, node])}
        """
        # model has read access for group E and F
        # field_a has a (python) group G
        # <div groups="A,B">
        #   <field name="field_a" invisible="field_b" groups="A,C"/>
        #   <field name="field_a" groups="B"/>
        #   <field name="field_c" required="field_a" groups="B1"/>
        #   <field name="field_c" required="field_a" groups="B2"/>
        # </div>
        #

        # views have many elements with the same groups
        parent = self
        while parent.parent:
            parent = parent.parent

        missing_fields = {}
        for name, groups_uses in self.used_fields.items():
            errors = []
            used = []

            for used_groups, (use, node) in groups_uses.items():
                available_info = self.available_fields.get(name, {})
                # Access is restricted to the administrator only. There is no need to check
                # groups as they are not used.
                if used_groups.is_empty():
                    if not available_info.get('groups', []):
                        used.append((used_groups, use, node))
                    continue

                # No match possible using only access right and groups on the field.
                if not (used_groups <= self._get_field_groups(name)):
                    errors.append((used_groups, use, node))
                    continue

                # At least one field in view match match with the used combinations.
                available_combined_groups = self.group_definitions.empty
                nodes_groups = available_info.get('groups', [])
                for groups in nodes_groups:
                    available_combined_groups |= groups

                if not (used_groups <= available_combined_groups):
                    used.append((used_groups, use, node))

            if errors:
                missing_fields[name] = (False, errors)
                continue

            if not used:
                continue

            missing_groups = self.group_definitions.empty
            for groups, _use, _node in used:
                missing_groups |= groups

            missing_fields[name] = (missing_groups, used)

        return missing_fields