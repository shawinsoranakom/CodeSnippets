def list_user_datasets_metadata(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
            return

        dataset_names = command_dict["dataset_names"]
        valid_datasets = []
        for dataset_name in dataset_names:
            dataset_id = self._get_dataset_id(dataset_name)
            if dataset_id is None:
                print(f"Dataset not found: {dataset_name}")
                continue
            valid_datasets.append((dataset_name, dataset_id))

        if not valid_datasets:
            print("No valid datasets found")
            return

        dataset_ids = [dataset_id for _, dataset_id in valid_datasets]
        kb_ids_param = ",".join(dataset_ids)
        response = self.http_client.request("GET", f"/kb/get_meta?kb_ids={kb_ids_param}",
                                            use_api_base=False, auth_kind="web")
        res_json = response.json()
        if response.status_code != 200:
            print(f"Fail to get metadata, code: {res_json.get('code')}, message: {res_json.get('message')}")
            return

        meta = res_json.get("data", {})
        if not meta:
            print("No metadata found")
            return

        table_data = []
        for field_name, values_dict in meta.items():
            for value, docs in values_dict.items():
                table_data.append({
                    "field": field_name,
                    "value": value,
                    "doc_ids": ", ".join(docs)
                })
        self._print_table_simple(table_data)