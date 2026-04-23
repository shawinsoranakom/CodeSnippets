def upload_documents(auth, payload=None, files_path=None, *, filename_override=None):
    # New endpoint: /api/v1/datasets/{kb_id}/documents
    kb_id = payload.get("kb_id") if payload else None
    url = f"{HOST_ADDRESS}/api/{VERSION}/datasets/{kb_id}/documents"

    if files_path is None:
        files_path = []

    fields = []
    file_objects = []
    try:
        # Note: kb_id is now in the URL path, not in the form data
        if payload:
            for k, v in payload.items():
                if k != "kb_id":  # Skip kb_id as it's in the URL
                    fields.append((k, str(v)))

        for fp in files_path:
            p = Path(fp)
            f = p.open("rb")
            filename = filename_override if filename_override is not None else p.name
            fields.append(("file", (filename, f)))
            file_objects.append(f)
        m = MultipartEncoder(fields=fields)

        res = requests.post(
            url=url,
            headers={"Content-Type": m.content_type},
            auth=auth,
            data=m,
        )
        return res.json()
    finally:
        for f in file_objects:
            f.close()