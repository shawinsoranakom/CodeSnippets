def state_forwards(self, app_label, state):
        state.alter_model_options(app_label, self.name_lower, {"db_table": self.table})