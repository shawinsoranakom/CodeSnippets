def _file_path_as_list(self) -> list[Data]:
        file_path = self.file_path
        if not file_path:
            return []

        def _message_to_data(message: Message) -> Data:
            return Data(**{self.SERVER_FILE_PATH_FIELDNAME: message.text})

        if isinstance(file_path, Data):
            file_path = [file_path]
        elif isinstance(file_path, Message):
            file_path = [_message_to_data(file_path)]
        elif not isinstance(file_path, list):
            msg = f"Expected list of Data objects in file_path but got {type(file_path)}."
            self.log(msg)
            if not self.silent_errors:
                raise ValueError(msg)
            return []

        file_paths = []
        for obj in file_path:
            data_obj = _message_to_data(obj) if isinstance(obj, Message) else obj

            if not isinstance(data_obj, Data):
                msg = f"Expected Data object in file_path but got {type(data_obj)}."
                self.log(msg)
                if not self.silent_errors:
                    raise ValueError(msg)
                continue
            file_paths.append(data_obj)

        return file_paths