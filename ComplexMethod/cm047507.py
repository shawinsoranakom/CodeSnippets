def init(self, db_name: str) -> None:
        self._init = True
        self.loaded = False
        self.ready = False

        self.models: dict[str, type[BaseModel]] = {}    # model name/model instance mapping
        self._sql_constraints = set()  # type: ignore
        self._database_translated_fields: dict[str, str] = {}  # names and translate function names of translated fields in database {"{model}.{field_name}": "translate_func"}
        self._database_company_dependent_fields: set[str] = set()  # names of company dependent fields in database
        if config['test_enable']:
            from odoo.tests.result import OdooTestResult  # noqa: PLC0415
            self._assertion_report: OdooTestResult | None = OdooTestResult()
        else:
            self._assertion_report = None
        self._ordinary_tables: set[str] | None = None  # cached names of regular tables
        self._constraint_queue: dict[typing.Any, Callable[[BaseCursor], None]] = {}  # queue of functions to call on finalization of constraints
        self.__caches: dict[str, LRU] = {cache_name: LRU(cache_size) for cache_name, cache_size in _REGISTRY_CACHES.items()}

        # update context during loading modules
        self._force_upgrade_scripts: set[str] = set()  # force the execution of the upgrade script for these modules
        self._reinit_modules: set[str] = set()  # modules to reinitialize

        # modules fully loaded (maintained during init phase by `loading` module)
        self._init_modules: set[str] = set()       # modules have been initialized
        self.updated_modules: list[str] = []       # installed/updated modules
        self.loaded_xmlids: set[str] = set()

        self.db_name = db_name
        self._db: Connection = sql_db.db_connect(db_name, readonly=False)
        self._db_readonly: Connection | None = None
        self._db_readonly_failed_time: float | None = None
        if config['db_replica_host'] or config['test_enable'] or 'replica' in config['dev_mode']:  # by default, only use readonly pool if we have a db_replica_host defined.
            self._db_readonly = sql_db.db_connect(db_name, readonly=True)

        # field dependencies
        self.field_depends: Collector[Field, Field] = Collector()
        self.field_depends_context: Collector[Field, str] = Collector()

        # field inverses
        self.many2many_relations: defaultdict[tuple[str, str, str], OrderedSet[tuple[str, str]]] = defaultdict(OrderedSet)

        # field setup dependents: this enables to invalidate the setup of
        # related fields when some of their dependencies are invalidated
        # (for incremental model setup)
        self.field_setup_dependents: Collector[Field, Field] = Collector()

        # company dependent
        self.many2one_company_dependents: Collector[str, Field] = Collector()  # {model_name: (field1, field2, ...)}

        # constraint checks
        self.not_null_fields: set[Field] = set()

        # cache of methods get_field_trigger_tree() and is_modifying_relations()
        self._field_trigger_trees: dict[Field, TriggerTree] = {}
        self._is_modifying_relations: dict[Field, bool] = {}

        # Inter-process signaling:
        # The `orm_signaling_registry` sequence indicates the whole registry
        # must be reloaded.
        # The `orm_signaling_... sequence` indicates the corresponding cache must be
        # invalidated (i.e. cleared).
        self.registry_sequence: int = -1
        self.cache_sequences: dict[str, int] = {}

        # Flags indicating invalidation of the registry or the cache.
        self._invalidation_flags = threading.local()

        from odoo.modules import db  # noqa: PLC0415
        with closing(self.cursor()) as cr:
            self.has_unaccent = db.has_unaccent(cr)
            self.has_trigram = db.has_trigram(cr)

        self.unaccent = _unaccent if self.has_unaccent else lambda x: x  # type: ignore
        self.unaccent_python = remove_accents if self.has_unaccent else lambda x: x