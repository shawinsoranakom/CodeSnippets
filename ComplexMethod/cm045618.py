def _traverse_objects_with_limit(self) -> list[GDriveFile]:
        files = []
        n_requests_done = 0
        queue: Queue[str] = Queue()
        reachable_folder_ids = set([self.root])

        queue.put(self.root)
        while not queue.empty():
            items: list[str] = []
            while len(items) < _MAX_ITEMS_PER_LIST_REQUEST and not queue.empty():
                items.append(queue.get())

            # We create and execute an API request to retrieve the contents of multiple
            # directories. Note that if there is a continuation token and we actually made
            # multiple requests, this will not be counted; we still count it as a single
            # request.
            query_parts = [f"'{item}' in parents" for item in items]
            parent_condition = " or ".join(query_parts)
            subitems = self._query(f"({parent_condition}) and trashed=false")
            n_requests_done += 1

            # Add files to the search result.
            files_found = [i for i in subitems if i["mimeType"] != MIME_TYPE_FOLDER]
            files.extend(files_found)

            # Put the subdirs to the queue.
            subdirs = [i["id"] for i in subitems if i["mimeType"] == MIME_TYPE_FOLDER]
            for subdir in subdirs:
                if subdir not in reachable_folder_ids:
                    reachable_folder_ids.add(subdir)
                    queue.put(subdir)

            # If the limit will be exceeded, terminate.
            n_requests_needed = queue.qsize() / _MAX_DIRECTORIES_FOR_TRAVERSAL
            if queue.qsize() % _MAX_DIRECTORIES_FOR_TRAVERSAL > 0:
                n_requests_needed += 1
            if n_requests_done + n_requests_needed > _MAX_DIRECTORIES_FOR_TRAVERSAL:
                raise _ListObjectsLimitExceeded()

        return files