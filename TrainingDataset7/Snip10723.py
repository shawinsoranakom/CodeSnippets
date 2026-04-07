def __init__(self, using, origin=None, force_collection=False):
        self.using = using
        # A Model or QuerySet object.
        self.origin = origin
        # Force collecting objects for deletion on the Python-level.
        self.force_collection = force_collection
        # Initially, {model: {instances}}, later values become lists.
        self.data = defaultdict(set)
        # {(field, value): [instances, …]}
        self.field_updates = defaultdict(list)
        # {model: {field: {instances}}}
        self.restricted_objects = defaultdict(partial(defaultdict, set))
        # fast_deletes is a list of queryset-likes that can be deleted without
        # fetching the objects into memory.
        self.fast_deletes = []

        # Tracks deletion-order dependency for databases without transactions
        # or ability to defer constraint checks. Only concrete model classes
        # should be included, as the dependencies exist only between actual
        # database tables; proxy models are represented here by their concrete
        # parent.
        self.dependencies = defaultdict(set)