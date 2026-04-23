def run(self):
        with optional_imports("pyfilesystem"):
            from fs.errors import ResourceNotFound as FSResourceNotFound

        while True:
            start_time = time.time()

            update = self._get_snapshot_update()
            for changed_path in update.changed_paths:
                try:
                    with self.source.open(changed_path) as file:
                        data = file.read()
                except FileNotFoundError:
                    logging.exception(
                        f"Failed to read file from {changed_path}. "
                        "Most likely it was deleted between the change "
                        "tracking and file read"
                    )
                    update.deleted_paths.append(changed_path)
                    continue

                data = data.encode("utf-8")

                provided_metadata = None
                if self.with_metadata:
                    try:
                        metadata = self.source.getinfo(
                            changed_path,
                            namespaces=[
                                "basic",
                                "details",
                                "access",
                            ],
                        )
                        metadata_dict = self._metadata_to_dict(changed_path, metadata)
                        provided_metadata = json.dumps(metadata_dict).encode("utf-8")
                    except FSResourceNotFound:
                        logging.exception(
                            f"Failed to acquire metadata for the object: {changed_path}"
                        )

                self._add(api.ref_scalar(changed_path), data, provided_metadata)
            for deleted_path in update.deleted_paths:
                self._remove(api.ref_scalar(deleted_path), b"")
                self.stored_modify_times.pop(deleted_path)
            self.commit()
            if self.mode == STATIC_MODE_NAME:
                break

            elapsed_time = time.time() - start_time
            if elapsed_time < self.refresh_interval:
                time.sleep(self.refresh_interval - elapsed_time)