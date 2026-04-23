def _check_fk_val(self):
            for field in self.field.foreign_related_fields:
                if getattr(self.instance, field.attname) is None:
                    raise ValueError(
                        f'"{self.instance!r}" needs to have a value for field '
                        f'"{field.attname}" before this relationship can be used.'
                    )