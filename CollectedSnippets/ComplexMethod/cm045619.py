def _detect_objects_with_full_scan(self) -> list[GDriveFile]:
        all_items = self._query("trashed=false")
        connections = defaultdict(list)
        for item in all_items:
            if item["mimeType"] != MIME_TYPE_FOLDER:
                # Don't build useless connections, we're only
                # interested in folder hierarchy
                continue

            parents = item.get("parents")
            if parents is not None:
                assert (
                    len(parents) == 1
                ), "GDrive API returned unexpected number of parents"
                parent_id = parents[0]
                connections[parent_id].append(item["id"])

        reachable_folder_ids = set([self.root])
        queue: Queue[str] = Queue()
        queue.put(self.root)
        while not queue.empty():
            item = queue.get()
            for nested_item in connections[item]:
                if nested_item not in reachable_folder_ids:
                    reachable_folder_ids.add(nested_item)
                    queue.put(nested_item)

        result_items = []
        for item in all_items:
            if item["mimeType"] == MIME_TYPE_FOLDER:
                continue

            parents = item.get("parents")
            if parents is not None:
                item_is_reachable = (
                    parents[0] in reachable_folder_ids or item["id"] == self.root
                )
            else:
                item_is_reachable = item["id"] == self.root

            if item_is_reachable:
                result_items.append(item)

        return result_items