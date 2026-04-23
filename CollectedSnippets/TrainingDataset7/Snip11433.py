def _check_unique(self, **kwargs):
        return (
            [
                checks.Warning(
                    "Setting unique=True on a ForeignKey has the same effect as using "
                    "a OneToOneField.",
                    hint=(
                        "ForeignKey(unique=True) is usually better served by a "
                        "OneToOneField."
                    ),
                    obj=self,
                    id="fields.W342",
                )
            ]
            if self.unique
            else []
        )