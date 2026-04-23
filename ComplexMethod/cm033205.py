def import_docs_into_dataset(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")

        dataset_name = command_dict["dataset_name"]
        dataset_id = self._get_dataset_id(dataset_name)
        if dataset_id is None:
            return

        document_paths = command_dict["document_paths"]
        paths = [Path(p) for p in document_paths]

        fields = []
        file_handles = []
        try:
            for path in paths:
                fh = path.open("rb")
                fields.append(("file", (path.name, fh)))
                file_handles.append(fh)
            fields.append(("kb_id", dataset_id))
            encoder = MultipartEncoder(fields=fields)
            headers = {"Content-Type": encoder.content_type}
            response = self.http_client.request(
                "POST",
                f"/datasets/{dataset_id}/documents?return_raw_files=true",
                headers=headers,
                data=encoder,
                json_body=None,
                params=None,
                stream=False,
                auth_kind="web",
                use_api_base=True
            )
            res = response.json()
            if res.get("code") == 0:
                print(f"Success to import documents into dataset {dataset_name}")
            else:
                print(f"Fail to import documents: code: {res['code']}, message: {res['message']}")
        except Exception as exc:
            print(f"Fail to import document into dataset: {dataset_name}, error: {exc}")
        finally:
            for fh in file_handles:
                fh.close()