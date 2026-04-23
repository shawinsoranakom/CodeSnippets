def get_pages(main_script_path_str: str) -> Dict[str, Dict[str, str]]:
    global _cached_pages

    # Avoid taking the lock if the pages cache hasn't been invalidated.
    pages = _cached_pages
    if pages is not None:
        return pages

    with _pages_cache_lock:
        # The cache may have been repopulated while we were waiting to grab
        # the lock.
        if _cached_pages is not None:
            return _cached_pages

        main_script_path = Path(main_script_path_str)
        main_page_icon, main_page_name = page_icon_and_name(main_script_path)
        main_page_script_hash = calc_md5(main_script_path_str)

        # NOTE: We include the page_script_hash in the dict even though it is
        #       already used as the key because that occasionally makes things
        #       easier for us when we need to iterate over pages.
        pages = {
            main_page_script_hash: {
                "page_script_hash": main_page_script_hash,
                "page_name": main_page_name,
                "icon": main_page_icon,
                "script_path": str(main_script_path.resolve()),
            }
        }

        pages_dir = main_script_path.parent / "pages"
        page_scripts = sorted(
            [f for f in pages_dir.glob("*.py") if not f.name.startswith(".")],
            key=page_sort_key,
        )

        for script_path in page_scripts:
            script_path_str = str(script_path.resolve())
            pi, pn = page_icon_and_name(script_path)
            psh = calc_md5(script_path_str)

            pages[psh] = {
                "page_script_hash": psh,
                "page_name": pn,
                "icon": pi,
                "script_path": script_path_str,
            }

        _cached_pages = pages

        return pages