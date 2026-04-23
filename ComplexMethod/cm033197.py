def list_user_dataset_documents(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")

        dataset_name = command_dict["dataset_name"]
        dataset_id = self._get_dataset_id(dataset_name)
        if dataset_id is None:
            return

        docs = self._list_documents(dataset_name, dataset_id)
        if docs is None:
            return

        if not docs:
            print(f"No documents found in dataset {dataset_name}")
            return

        print(f"Documents in dataset: {dataset_name}")
        print("-" * 60)
        # Select key fields for display
        display_docs = []
        for doc in docs:
            meta_fields = doc.get("meta_fields", {})
            # Convert meta_fields dict to string for display
            meta_fields_str = ""
            if meta_fields:
                meta_fields_str = str(meta_fields)
            display_doc = {
                "name": doc.get("name", ""),
                "id": doc.get("id", ""),
                "size": doc.get("size", 0),
                "status": doc.get("status", ""),
                "created_at": doc.get("created_at", ""),
            }
            if meta_fields_str:
                display_doc["meta_fields"] = meta_fields_str
            display_docs.append(display_doc)
        self._print_table_simple(display_docs)