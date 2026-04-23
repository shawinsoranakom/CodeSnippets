def _list_files_recursive(
        self, 
        path: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[str, dict]]:
        """Recursively list all files in the given path

        Args:
            path: Path to list files from
            start: Start datetime for filtering
            end: End datetime for filtering

        Returns:
            List of tuples containing (file_path, file_info)
        """
        if self.client is None:
            raise ConnectorMissingCredentialError("WebDAV client not initialized")

        files = []

        try:
            logging.debug(f"Listing directory: {path}")
            for item in self.client.ls(path, detail=True):
                item_path = item['name']

                if item_path == path or item_path == path + '/':
                    continue

                logging.debug(f"Found item: {item_path}, type: {item.get('type')}")

                if item.get('type') == 'directory':
                    try:
                        files.extend(self._list_files_recursive(item_path, start, end))
                    except Exception as e:
                        logging.error(f"Error recursing into directory {item_path}: {e}")
                        continue
                else:
                    try:
                        file_name = os.path.basename(item_path)
                        if not self._is_supported_file(file_name):
                            logging.debug(f"Skipping file {item_path} due to unsupported extension.")
                            continue

                        modified_time = item.get('modified')
                        if modified_time:
                            if isinstance(modified_time, datetime):
                                modified = modified_time
                                if modified.tzinfo is None:
                                    modified = modified.replace(tzinfo=timezone.utc)
                            elif isinstance(modified_time, str):
                                try:
                                    modified = datetime.strptime(modified_time, '%a, %d %b %Y %H:%M:%S %Z')
                                    modified = modified.replace(tzinfo=timezone.utc)
                                except (ValueError, TypeError):
                                    try:
                                        modified = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                                    except (ValueError, TypeError):
                                        logging.warning(f"Could not parse modified time for {item_path}: {modified_time}")
                                        modified = datetime.now(timezone.utc)
                            else:
                                modified = datetime.now(timezone.utc)
                        else:
                            modified = datetime.now(timezone.utc)


                        logging.debug(f"File {item_path}: modified={modified}, start={start}, end={end}, include={start < modified <= end}")
                        if start < modified <= end:
                            files.append((item_path, item))
                        else:
                            logging.debug(f"File {item_path} filtered out by time range")
                    except Exception as e:
                        logging.error(f"Error processing file {item_path}: {e}")
                        continue

        except Exception as e:
            logging.error(f"Error listing directory {path}: {e}")

        return files