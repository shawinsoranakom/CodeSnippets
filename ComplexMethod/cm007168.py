def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        file_paths = [str(file.path) for file in file_list if file.path]

        if not file_paths:
            self.log("No files to process.")
            return file_list

        # https://docs.unstructured.io/api-reference/api-services/api-parameters
        args = self.unstructured_args or {}

        if self.chunking_strategy:
            args["chunking_strategy"] = self.chunking_strategy

        args["api_key"] = self.api_key
        args["partition_via_api"] = True
        if self.api_url:
            args["url"] = self.api_url

        loader = UnstructuredLoader(
            file_paths,
            **args,
        )

        documents = loader.load()

        processed_data: list[Data | None] = [Data.from_document(doc) if doc else None for doc in documents]

        # Rename the `source` field to `self.SERVER_FILE_PATH_FIELDNAME`, to avoid conflicts with the `source` field
        for data in processed_data:
            if data and "source" in data.data:
                data.data[self.SERVER_FILE_PATH_FIELDNAME] = data.data.pop("source")

        return self.rollup_data(file_list, processed_data)