def run(self) -> None:
        from googleapiclient.errors import HttpError

        client = _GDriveClient(
            self._root,
            self._credentials_factory(),
            self._object_size_limit,
            self._file_name_pattern,
            self._list_objects_strategy,
        )
        prev = _GDriveTree({})

        while True:
            try:
                tree = client.tree()
            except HttpError as e:
                logging.error(
                    f"Failed to query GDrive: {e}. Retrying in {self._refresh_interval} seconds...",
                )
            else:
                for file in tree.removed_files(prev):
                    self.remove(file)
                for file in tree.new_and_changed_files(prev):
                    payload = (
                        uuid.uuid4().bytes  # Trigger a change inside UpsertSession
                        if self._only_metadata
                        else client.download(file)
                    )
                    if payload is not None:
                        self.upsert(file, payload)

                if self._mode == "static":
                    break
                prev = tree
            time.sleep(self._refresh_interval)