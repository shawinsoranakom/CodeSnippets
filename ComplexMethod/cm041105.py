def backend_model_apply_operations(self, patch_operations):
        # run pre-actions
        if isinstance(self, apigateway_models.Stage) and [
            op for op in patch_operations if "/accessLogSettings" in op.get("path", "")
        ]:
            self.access_log_settings = self.access_log_settings or {}
        # apply patches
        apply_json_patch_safe(self, patch_operations, in_place=True)
        # run post-actions
        if isinstance(self, apigateway_models.Stage):
            bool_params = ["cacheClusterEnabled", "tracingEnabled"]
            for bool_param in bool_params:
                if getattr(self, camelcase_to_underscores(bool_param), None):
                    value = getattr(self, camelcase_to_underscores(bool_param), None)
                    setattr(self, camelcase_to_underscores(bool_param), str_to_bool(value))
        return self