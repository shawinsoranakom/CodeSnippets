def animal_pre_save_check(self, signal, sender, instance, **kwargs):
        self.pre_save_checks.append(
            (
                "Count = %s (%s)" % (instance.count, type(instance.count)),
                "Weight = %s (%s)" % (instance.weight, type(instance.weight)),
            )
        )