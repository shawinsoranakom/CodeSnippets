def allows_group_by_selected_pks_on_model(self, model):
        if not self.allows_group_by_selected_pks:
            return False
        return model._meta.managed