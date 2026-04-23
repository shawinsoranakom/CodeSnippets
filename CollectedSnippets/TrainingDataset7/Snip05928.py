def __init__(self, *args, force_collection=True, **kwargs):
        super().__init__(*args, force_collection=force_collection, **kwargs)
        self.edges = {}  # {from_instance: [to_instances]}
        self.protected = set()
        self.model_objs = defaultdict(set)