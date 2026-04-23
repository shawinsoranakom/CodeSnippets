def upload_documents(client: HttpClient, dataset_id: str, file_paths: Iterable[str]) -> List[Dict[str, Any]]:
    paths = [Path(p) for p in file_paths]
    if MultipartEncoder is None:
        files = [("file", (p.name, p.open("rb"))) for p in paths]
        try:
            response = client.request(
                "POST",
                f"/datasets/{dataset_id}/documents",
                headers=None,
                data=None,
                json_body=None,
                files=files,
                params=None,
                stream=False,
                auth_kind="api",
            )
        finally:
            for _, (_, fh) in files:
                fh.close()
        res = response.json()
    else:
        fields = []
        file_handles = []
        try:
            for path in paths:
                fh = path.open("rb")
                fields.append(("file", (path.name, fh)))
                file_handles.append(fh)
            encoder = MultipartEncoder(fields=fields)
            headers = {"Content-Type": encoder.content_type}
            response = client.request(
                "POST",
                f"/datasets/{dataset_id}/documents",
                headers=headers,
                data=encoder,
                json_body=None,
                params=None,
                stream=False,
                auth_kind="api",
            )
            res = response.json()
        finally:
            for fh in file_handles:
                fh.close()
    if res.get("code") != 0:
        raise DatasetError(f"Upload documents failed: {res.get('message')}")
    return res.get("data", [])