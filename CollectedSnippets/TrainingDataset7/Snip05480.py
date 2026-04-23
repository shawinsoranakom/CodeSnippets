def __init__(self, installed_apps=()):
        # installed_apps is set to None when creating the main registry
        # because it cannot be populated at that point. Other registries must
        # provide a list of installed apps and are populated immediately.
        if installed_apps is None and hasattr(sys.modules[__name__], "apps"):
            raise RuntimeError("You must supply an installed_apps argument.")

        # Mapping of app labels => model names => model classes. Every time a
        # model is imported, ModelBase.__new__ calls apps.register_model which
        # creates an entry in all_models. All imported models are registered,
        # regardless of whether they're defined in an installed application
        # and whether the registry has been populated. Since it isn't possible
        # to reimport a module safely (it could reexecute initialization code)
        # all_models is never overridden or reset.
        self.all_models = defaultdict(dict)

        # Mapping of labels to AppConfig instances for installed apps.
        self.app_configs = {}

        # Stack of app_configs. Used to store the current state in
        # set_available_apps and set_installed_apps.
        self.stored_app_configs = []

        # Whether the registry is populated.
        self.apps_ready = self.models_ready = self.ready = False
        # For the autoreloader.
        self.ready_event = threading.Event()

        # Lock for thread-safe population.
        self._lock = threading.RLock()
        self.loading = False

        # Maps ("app_label", "modelname") tuples to lists of functions to be
        # called when the corresponding model is ready. Used by this class's
        # `lazy_model_operation()` and `do_pending_operations()` methods.
        self._pending_operations = defaultdict(list)

        # Populate apps and models, unless it's the main registry.
        if installed_apps is not None:
            self.populate(installed_apps)