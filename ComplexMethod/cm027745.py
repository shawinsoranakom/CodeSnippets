def _deep_reload(module: Module, reloaded_modules_tracker: set[str]):
        """
        Recursively reloads modules imported by the given module.

        Only user-defined modules are reloaded, see `is_user_defined_module()`.
        """
        ignore_manimlib_modules = manim_config.ignore_manimlib_modules_on_reload
        if ignore_manimlib_modules and module.__name__.startswith("manimlib"):
            return
        if module.__name__.startswith("manimlib.config"):
            # We don't want to reload global manim_config
            return

        if not hasattr(module, "__dict__"):
            return

        # Prevent reloading the same module multiple times
        if module.__name__ in reloaded_modules_tracker:
            return
        reloaded_modules_tracker.add(module.__name__)

        # Recurse for all imported modules
        for _attr_name, attr_value in module.__dict__.items():
            if isinstance(attr_value, Module):
                if ModuleLoader._is_user_defined_module(attr_value.__name__):
                    ModuleLoader._deep_reload(attr_value, reloaded_modules_tracker)

            # Also reload modules that are part of a class or function
            # e.g. when importing `from custom_module import CustomClass`
            elif hasattr(attr_value, "__module__"):
                attr_module_name = attr_value.__module__
                if ModuleLoader._is_user_defined_module(attr_module_name):
                    attr_module = sys.modules[attr_module_name]
                    ModuleLoader._deep_reload(attr_module, reloaded_modules_tracker)

        # Reload
        log.debug('Reloading module "%s"', module.__name__)
        importlib.reload(module)