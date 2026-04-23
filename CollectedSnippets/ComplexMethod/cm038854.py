def summarize_results(results: dict[str, AutotuneResult]) -> bool:
    logger.info("=" * 50)
    logger.info("Autotuning Results Summary")
    logger.info("=" * 50)

    total_successful = 0
    total_failed = 0
    success_kernels = []
    partial_kernels = []
    error_kernels = []
    skipped_kernels = []

    for kernel_name, result in results.items():
        total_successful += result.successful
        total_failed += result.failed

        if result.status == "success":
            success_kernels.append(f"{kernel_name} ({result.successful} configs)")
            logger.info("✓ %s: %d configs successful", kernel_name, result.successful)
        elif result.status == "partial":
            partial_kernels.append(
                f"{kernel_name} ({result.successful} ok, {result.failed} failed)"
            )
            logger.warning(
                "⚠ %s: %d successful, %d failed",
                kernel_name,
                result.successful,
                result.failed,
            )
        elif result.status == "error":
            error_kernels.append(f"{kernel_name}: {result.message or 'Unknown error'}")
            logger.error("✗ %s: %s", kernel_name, result.message or "Unknown error")
        elif result.status == "skipped":
            skipped_kernels.append(f"{kernel_name}: {result.message or 'Skipped'}")
            logger.info("- %s: %s", kernel_name, result.message or "Skipped")

    logger.info("=" * 50)
    logger.info(
        "Summary: %d total configs (%d successful, %d failed)",
        total_successful + total_failed,
        total_successful,
        total_failed,
    )
    logger.info(
        "Kernels: %d success, %d partial, %d error, %d skipped",
        len(success_kernels),
        len(partial_kernels),
        len(error_kernels),
        len(skipped_kernels),
    )

    has_failures = bool(error_kernels or partial_kernels)

    if not has_failures:
        if total_successful > 0:
            logger.info("All configs autotuned successfully!")
        else:
            logger.info("No new configs were generated (all may already exist)")

    return not has_failures