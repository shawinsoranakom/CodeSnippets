def model_patches_call_function(self, function_name="cleanup", arguments={}):
        to = self.model_options["transformer_options"]
        if "patches" in to:
            patches = to["patches"]
            for name in patches:
                patch_list = patches[name]
                for i in range(len(patch_list)):
                    if hasattr(patch_list[i], function_name):
                        getattr(patch_list[i], function_name)(**arguments)
        if "patches_replace" in to:
            patches = to["patches_replace"]
            for name in patches:
                patch_list = patches[name]
                for k in patch_list:
                    if hasattr(patch_list[k], function_name):
                        getattr(patch_list[k], function_name)(**arguments)
        if "model_function_wrapper" in self.model_options:
            wrap_func = self.model_options["model_function_wrapper"]
            if hasattr(wrap_func, function_name):
                getattr(wrap_func, function_name)(**arguments)