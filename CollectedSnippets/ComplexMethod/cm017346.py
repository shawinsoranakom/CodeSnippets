def _check_field_name_clashes(cls):
        """Forbid field shadowing in multi-table inheritance."""
        errors = []
        used_fields = {}  # name or attname -> field

        # Check that multi-inheritance doesn't cause field name shadowing.
        for parent in cls._meta.all_parents:
            for f in parent._meta.local_fields:
                clash = used_fields.get(f.name) or used_fields.get(f.attname) or None
                if clash:
                    errors.append(
                        checks.Error(
                            "The field '%s' from parent model "
                            "'%s' clashes with the field '%s' "
                            "from parent model '%s'."
                            % (clash.name, clash.model._meta, f.name, f.model._meta),
                            obj=cls,
                            id="models.E005",
                        )
                    )
                used_fields[f.name] = f
                used_fields[f.attname] = f

        # Check that fields defined in the model don't clash with fields from
        # parents, including auto-generated fields like multi-table inheritance
        # child accessors.
        for parent in cls._meta.all_parents:
            for f in parent._meta.get_fields():
                if f not in used_fields:
                    used_fields[f.name] = f

        # Check that parent links in diamond-shaped MTI models don't clash.
        for parent_link in cls._meta.parents.values():
            if not parent_link:
                continue
            clash = used_fields.get(parent_link.name) or None
            if clash:
                errors.append(
                    checks.Error(
                        f"The field '{parent_link.name}' clashes with the field "
                        f"'{clash.name}' from model '{clash.model._meta}'.",
                        obj=cls,
                        id="models.E006",
                    )
                )

        for f in cls._meta.local_fields:
            clash = used_fields.get(f.name) or used_fields.get(f.attname) or None
            # Note that we may detect clash between user-defined non-unique
            # field "id" and automatically added unique field "id", both
            # defined at the same model. This special case is considered in
            # _check_id_field and here we ignore it.
            id_conflict = (
                f.name == "id" and clash and clash.name == "id" and clash.model == cls
            )
            if clash and not id_conflict:
                errors.append(
                    checks.Error(
                        "The field '%s' clashes with the field '%s' "
                        "from model '%s'." % (f.name, clash.name, clash.model._meta),
                        obj=f,
                        id="models.E006",
                    )
                )
            used_fields[f.name] = f
            used_fields[f.attname] = f

        return errors