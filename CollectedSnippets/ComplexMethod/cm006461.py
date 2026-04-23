async def cancel_ingestion(
    kb_name: str,
    current_user: CurrentActiveUser,
    job_service: Annotated[JobService, Depends(get_job_service)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> dict[str, str]:
    """Cancel the ongoing ingestion task for a knowledge base."""
    try:
        kb_path = _resolve_kb_path(kb_name, current_user)

        # Get KB metadata to extract asset_id
        metadata = KBAnalysisHelper.get_metadata(kb_path, fast=True)
        asset_id_str = metadata.get("id")

        if not asset_id_str:
            raise HTTPException(status_code=400, detail="Knowledge base missing asset ID")

        try:
            asset_id = uuid.UUID(asset_id_str)
        except (ValueError, AttributeError) as e:
            raise HTTPException(status_code=400, detail="Invalid asset ID") from e

        # Fetch the latest ingestion job for this KB
        latest_jobs = await job_service.get_latest_jobs_by_asset_ids([asset_id])

        if asset_id not in latest_jobs:
            raise HTTPException(status_code=404, detail=f"No ingestion job found for the knowledge base {kb_name}")

        job = latest_jobs[asset_id]
        job_status = job.status.value if hasattr(job.status, "value") else str(job.status)

        # Check if job is already completed or failed
        if job_status in ["completed", "failed", "cancelled", "timed_out"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status '{job_status}'")

        revoked = await task_service.revoke_task(job.job_id)
        # Update status immediately so background task can see it
        await job_service.update_job_status(job.job_id, JobStatus.CANCELLED)

        # Clean up any partially ingested chunks from this job
        await KBIngestionHelper.cleanup_chroma_chunks_by_job(job.job_id, kb_path, kb_name)

        if revoked:
            message = f"Ingestion job for {job.job_id} cancelled successfully."
        else:
            message = f"Job {job.job_id} is already cancelled."
    except asyncio.CancelledError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("Error cancelling ingestion: %s", e)
        raise HTTPException(status_code=500, detail="Error cancelling ingestion.") from e
    else:
        return {"message": message}