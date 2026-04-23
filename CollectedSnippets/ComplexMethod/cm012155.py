def __init__(self, nodes: list[fx.Node]):
        # Map from node to the fresh storages it allocates (not views/aliases)
        self.node_to_fresh_allocations: dict[fx.Node, OrderedSet[StorageKey]] = {}

        # Map from storage to the node that originally allocated it
        self.storage_to_allocator: dict[StorageKey, fx.Node] = {}

        # Map from node to all storages it uses as inputs
        self.node_to_storage_uses: dict[fx.Node, OrderedSet[StorageKey]] = {}

        # Map from storage to all nodes that use it
        self.storage_to_uses: dict[StorageKey, OrderedSet[fx.Node]] = defaultdict(
            OrderedSet
        )

        # Map from storage to the last node that uses it
        self.storage_to_last_user: dict[StorageKey, fx.Node] = {}

        # Map from node to storages that have their last use at that node
        self.node_to_storages_last_used: dict[fx.Node, OrderedSet[StorageKey]] = (
            defaultdict(OrderedSet)
        )

        # Track all output storages for each node (for building usage graph)
        self.node_to_output_storages: dict[fx.Node, OrderedSet[StorageKey]] = {}

        # First pass: build storage allocations and track uses
        for node in nodes:
            # Get output storages
            output_storages = self._get_output_storages(node)
            self.node_to_output_storages[node] = output_storages

            # Track fresh allocations
            fresh_allocations: OrderedSet[StorageKey] = OrderedSet()
            for storage_key in output_storages:
                if storage_key not in self.storage_to_allocator:
                    self.storage_to_allocator[storage_key] = node
                    fresh_allocations.add(storage_key)
            self.node_to_fresh_allocations[node] = fresh_allocations

            # Track input storage uses (safe because inputs were already processed)
            input_storages = self._get_input_storages(node)
            self.node_to_storage_uses[node] = input_storages
            for storage_key in input_storages:
                self.storage_to_uses[storage_key].add(node)

        # Second pass: find last users (iterate in reverse)
        for node in reversed(nodes):
            input_storages = self.node_to_storage_uses[node]
            for storage_key in input_storages:
                if storage_key not in self.storage_to_last_user:
                    self.storage_to_last_user[storage_key] = node
                    self.node_to_storages_last_used[node].add(storage_key)