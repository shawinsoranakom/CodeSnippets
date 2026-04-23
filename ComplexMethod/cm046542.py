async def delete_cached_model(
    repo_id: str = Body(...),
    variant: Optional[str] = Body(None),
    current_subject: str = Depends(get_current_subject),
):
    """Delete a cached model repo (or a specific GGUF variant) from the HF cache.

    When *variant* is provided, only the GGUF files matching that quant label
    are removed (e.g. ``UD-Q4_K_XL``).  Otherwise the entire repo is deleted.
    Refuses if the model is currently loaded for inference.
    """
    if not _is_valid_repo_id(repo_id):
        raise HTTPException(status_code = 400, detail = "Invalid repo_id format")

    # Check if model is currently loaded
    try:
        from routes.inference import get_llama_cpp_backend

        llama_backend = get_llama_cpp_backend()
        if llama_backend.is_loaded and llama_backend.model_identifier:
            loaded_id = llama_backend.model_identifier.lower()
            if loaded_id == repo_id.lower() or loaded_id.startswith(repo_id.lower()):
                raise HTTPException(
                    status_code = 400,
                    detail = "Unload the model before deleting",
                )
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        inference_backend = get_inference_backend()
        if inference_backend.active_model_name:
            active = inference_backend.active_model_name.lower()
            if active == repo_id.lower() or active.startswith(repo_id.lower()):
                raise HTTPException(
                    status_code = 400,
                    detail = "Unload the model before deleting",
                )
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        cache_scans = _all_hf_cache_scans()

        target_repo = None
        for hf_cache in cache_scans:
            for repo_info in hf_cache.repos:
                if repo_info.repo_type != "model":
                    continue
                if repo_info.repo_id.lower() == repo_id.lower():
                    target_repo = repo_info
                    break
            if target_repo is not None:
                break

        if target_repo is None:
            raise HTTPException(status_code = 404, detail = "Model not found in cache")

        # ── Per-variant GGUF deletion ────────────────────────────
        if variant:
            deleted_bytes = 0
            deleted_count = 0
            for rev in target_repo.revisions:
                for f in rev.files:
                    if not _is_gguf_filename(f.file_name):
                        continue
                    quant = _extract_quant_label(f.file_name)
                    if quant.lower() != variant.lower():
                        continue
                    # Delete the blob (actual data) and the snapshot symlink
                    try:
                        blob = Path(f.blob_path)
                        snap = Path(f.file_path)
                        size = blob.stat().st_size if blob.exists() else 0
                        if snap.exists() or snap.is_symlink():
                            snap.unlink()
                        if blob.exists():
                            blob.unlink()
                        deleted_bytes += size
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {f.file_name}: {e}")

            if deleted_count == 0:
                raise HTTPException(
                    status_code = 404,
                    detail = f"Variant {variant} not found in cache for {repo_id}",
                )

            freed_mb = deleted_bytes / (1024 * 1024)
            logger.info(
                f"Deleted {deleted_count} file(s) for {repo_id} variant {variant}: "
                f"{freed_mb:.1f} MB freed"
            )
            return {"status": "deleted", "repo_id": repo_id, "variant": variant}

        # ── Full repo deletion ───────────────────────────────────
        revision_hashes = [rev.commit_hash for rev in target_repo.revisions]
        if not revision_hashes:
            raise HTTPException(status_code = 404, detail = "No revisions found for model")

        delete_strategy = hf_cache.delete_revisions(*revision_hashes)
        logger.info(
            f"Deleting cached model {repo_id}: "
            f"{delete_strategy.expected_freed_size_str} will be freed"
        )
        delete_strategy.execute()

        return {"status": "deleted", "repo_id": repo_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cached model {repo_id}: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to delete cached model: {str(e)}",
        )