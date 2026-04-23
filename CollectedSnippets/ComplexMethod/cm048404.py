def _run_least_packages_removal_strategy_astar(self, domain, qty):
        # Fetch the available packages and contents
        domain = Domain(domain).optimize(self)
        query = self._search(domain, bypass_access=True)
        query.groupby = SQL("package_id")
        query.having = SQL("SUM(quantity - reserved_quantity) > 0")
        query.order = SQL("available_qty DESC")
        qty_by_package = self.env.execute_query(
            query.select('package_id', 'SUM(quantity - reserved_quantity) AS available_qty'))

        # Items that do not belong to a package are added individually to the list, any empty packages get removed.
        pkg_found = False
        new_qty_by_package = []
        none_elements = []

        for elem in qty_by_package:
            if elem[0] is None:
                none_elements.extend([(None, 1) for _ in range(int(elem[1]))])
            elif elem[1] != 0:
                new_qty_by_package.append(elem)
                pkg_found = True

        new_qty_by_package.extend(none_elements)
        qty_by_package = new_qty_by_package

        if not pkg_found:
            return domain
        size = len(qty_by_package)

        class PriorityQueue:
            def __init__(self):
                self.elements = []

            def empty(self) -> bool:
                return not self.elements

            def put(self, item, priority):
                heapq.heappush(self.elements, (priority, item))

            def get(self):
                return heapq.heappop(self.elements)[1]

        def heuristic(node):
            if node.next_index < size:
                return len(node.taken_packages) + node.count_remaining / qty_by_package[node.next_index][1]
            return len(node.taken_packages)

        def generate_domain(node):
            selected_single_items = []
            single_item_ids = False
            for pkg in node.taken_packages:
                if pkg[0] is None:
                    # Lazily retrieve ids for single items
                    if not single_item_ids:
                        single_item_ids = self.search(Domain('package_id', '=', None) & domain).ids
                    selected_single_items.append(single_item_ids.pop())

            return (
                Domain('package_id', 'in', [elem[0] for elem in node.taken_packages if elem[0] is not None])
                | Domain('id', 'in', selected_single_items)
            ) & domain

        Node = namedtuple("Node", "count_remaining taken_packages next_index")

        frontier = PriorityQueue()
        frontier.put(Node(qty, (), 0), 0)

        best_leaf = Node(qty, (), 0)

        try:
            while not frontier.empty():
                current = frontier.get()

                if current.count_remaining <= 0:
                    return generate_domain(current)

                # Keep track of processed package amounts to only generate one branch for the same amount
                last_count = None
                i = current.next_index
                while i < size:
                    pkg = qty_by_package[i]
                    i += 1
                    if pkg[1] == last_count:
                        continue
                    last_count = pkg[1]

                    count = current.count_remaining - pkg[1]
                    taken = current.taken_packages + (pkg,)
                    node = Node(count, taken, i)

                    if count < 0:
                        # Overselect case
                        if best_leaf.count_remaining > 0 or len(node.taken_packages) < len(best_leaf.taken_packages) or (len(node.taken_packages) == len(best_leaf.taken_packages) and node.count_remaining > best_leaf.count_remaining):
                            best_leaf = node
                        continue

                    if i >= size and count != 0:
                        # Not enough packages case
                        if node.count_remaining < best_leaf.count_remaining:
                            best_leaf = node
                        continue

                    frontier.put(node, heuristic(node))
        except MemoryError:
            _logger.info('Ran out of memory while trying to use the least_packages strategy to get quants. Domain: %s', domain)
            return domain

        # no exact matching possible, use best leaf
        return generate_domain(best_leaf)