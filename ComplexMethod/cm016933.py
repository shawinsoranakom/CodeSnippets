async def upload_asset(request: web.Request) -> web.Response:
    """Multipart/form-data endpoint for Asset uploads."""
    try:
        parsed = await parse_multipart_upload(request, check_hash_exists=asset_exists)
    except UploadError as e:
        return _build_error_response(e.status, e.code, e.message)

    owner_id = USER_MANAGER.get_request_user_id(request)

    try:
        spec = schemas_in.UploadAssetSpec.model_validate(
            {
                "tags": parsed.tags_raw,
                "name": parsed.provided_name,
                "user_metadata": parsed.user_metadata_raw,
                "hash": parsed.provided_hash,
                "mime_type": parsed.provided_mime_type,
                "preview_id": parsed.provided_preview_id,
            }
        )
    except ValidationError as ve:
        delete_temp_file_if_exists(parsed.tmp_path)
        return _build_error_response(
            400, "INVALID_BODY", f"Validation failed: {ve.json()}"
        )

    if spec.tags and spec.tags[0] == "models":
        if (
            len(spec.tags) < 2
            or spec.tags[1] not in folder_paths.folder_names_and_paths
        ):
            delete_temp_file_if_exists(parsed.tmp_path)
            category = spec.tags[1] if len(spec.tags) >= 2 else ""
            return _build_error_response(
                400, "INVALID_BODY", f"unknown models category '{category}'"
            )

    try:
        # Fast path: hash exists, create AssetReference without writing anything
        if spec.hash and parsed.provided_hash_exists is True:
            result = create_from_hash(
                hash_str=spec.hash,
                name=spec.name or (spec.hash.split(":", 1)[1]),
                tags=spec.tags,
                user_metadata=spec.user_metadata or {},
                owner_id=owner_id,
                mime_type=spec.mime_type,
                preview_id=spec.preview_id,
            )
            if result is None:
                delete_temp_file_if_exists(parsed.tmp_path)
                return _build_error_response(
                    404, "ASSET_NOT_FOUND", f"Asset content {spec.hash} does not exist"
                )
            delete_temp_file_if_exists(parsed.tmp_path)
        else:
            # Otherwise, we must have a temp file path to ingest
            if not parsed.tmp_path or not os.path.exists(parsed.tmp_path):
                return _build_error_response(
                    400,
                    "MISSING_INPUT",
                    "Provided hash not found and no file uploaded.",
                )

            result = upload_from_temp_path(
                temp_path=parsed.tmp_path,
                name=spec.name,
                tags=spec.tags,
                user_metadata=spec.user_metadata or {},
                client_filename=parsed.file_client_name,
                owner_id=owner_id,
                expected_hash=spec.hash,
                mime_type=spec.mime_type,
                preview_id=spec.preview_id,
            )
    except AssetValidationError as e:
        delete_temp_file_if_exists(parsed.tmp_path)
        return _build_error_response(400, e.code, str(e))
    except ValueError as e:
        delete_temp_file_if_exists(parsed.tmp_path)
        return _build_error_response(400, "BAD_REQUEST", str(e))
    except HashMismatchError as e:
        delete_temp_file_if_exists(parsed.tmp_path)
        return _build_error_response(400, "HASH_MISMATCH", str(e))
    except DependencyMissingError as e:
        delete_temp_file_if_exists(parsed.tmp_path)
        return _build_error_response(503, "DEPENDENCY_MISSING", e.message)
    except Exception:
        delete_temp_file_if_exists(parsed.tmp_path)
        logging.exception("upload_asset failed for owner_id=%s", owner_id)
        return _build_error_response(500, "INTERNAL", "Unexpected server error.")

    asset = _build_asset_response(result)
    payload_out = schemas_out.AssetCreated(
        **asset.model_dump(),
        created_new=result.created_new,
    )
    status = 201 if result.created_new else 200
    return web.json_response(payload_out.model_dump(mode="json", exclude_none=True), status=status)