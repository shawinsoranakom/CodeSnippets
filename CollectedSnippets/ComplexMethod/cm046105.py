def _load_images_from_pdf_bytes_range(
    pdf_bytes: bytes,
    dpi=DEFAULT_PDF_IMAGE_DPI,
    start_page_id=0,
    end_page_id=0,
    image_type=ImageType.PIL,
    timeout=None,
    threads=None,
):
    if end_page_id < start_page_id:
        return []

    if timeout is None:
        timeout = get_load_images_timeout()
    if threads is None:
        threads = get_load_images_threads()

    actual_threads, page_ranges = _get_render_process_plan(
        start_page_id,
        end_page_id,
        threads,
    )

    logger.debug(
        f"PDF image rendering uses {actual_threads} processes for pages "
        f"{start_page_id + 1}-{end_page_id + 1}: {page_ranges}"
    )

    executor = _get_pdf_render_executor()
    recycle_executor = False
    try:
        futures = []
        future_to_range = {}
        for range_start, range_end in page_ranges:
            future = executor.submit(
                _load_images_from_pdf_worker,
                pdf_bytes,
                dpi,
                range_start,
                range_end,
                image_type,
            )
            futures.append(future)
            future_to_range[future] = range_start

        _, not_done = wait(futures, timeout=timeout, return_when=ALL_COMPLETED)
        if not_done:
            recycle_executor = True
            raise TimeoutError(
                f"PDF image rendering timeout after {timeout}s "
                f"for pages {start_page_id + 1}-{end_page_id + 1}"
            )

        all_results = []
        for future in futures:
            range_start = future_to_range[future]
            images_list = future.result()
            all_results.append((range_start, images_list))

        all_results.sort(key=lambda x: x[0])
        images_list = []
        for _, imgs in all_results:
            images_list.extend(imgs)

        return images_list
    except BrokenProcessPool:
        recycle_executor = True
        raise
    finally:
        if recycle_executor:
            logger.warning("Recycling persistent PDF render executor after render failure")
            _recycle_pdf_render_executor(
                executor,
                terminate_processes=True,
            )