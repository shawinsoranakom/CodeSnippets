async def download_data(urls, use_cache: bool = True):  # noqa: PLR0915
    """Get the Form 4 data from a list of URLs."""
    # pylint: disable=import-outside-toplevel
    import asyncio  # noqa
    import os
    import sqlite3
    from numpy import nan
    from openbb_core.app.utils import get_user_cache_directory
    from pandas import DataFrame

    results: list = []
    non_cached_urls: list = []

    try:
        if use_cache is True:
            db_dir = f"{get_user_cache_directory()}/sql"
            db_path = f"{db_dir}/sec_form4.db"
            # Decompress the database file
            if os.path.exists(f"{db_path}.gz"):
                decompress_db(db_path)

            os.makedirs(db_dir, exist_ok=True)

            try:
                conn = sqlite3.connect(db_path)
                setup_database(conn)
                cached_data = get_cached_data(urls, conn)
                cached_urls = {entry["filing_url"] for entry in cached_data}
                for url in urls:
                    if url not in cached_urls:
                        non_cached_urls.append(url)
            except sqlite3.DatabaseError as e:
                logger.info("Error connecting to the database.")
                retry_input = input(
                    "Would you like to retry with a new database? (y/n): "
                )
                if retry_input.lower() == "y":
                    faulty_db_path = f"{db_path}.faulty"
                    os.rename(db_path, faulty_db_path)
                    logger.info("Renamed faulty database to %s", faulty_db_path)
                    db_path = f"{db_dir}/sec_form4.db"
                    conn = sqlite3.connect(db_path)
                    setup_database(conn)
                    cached_data = get_cached_data(urls, conn)
                    cached_urls = {entry["filing_url"] for entry in cached_data}
                    for url in urls:
                        if url not in cached_urls:
                            non_cached_urls.append(url)
                else:
                    raise OpenBBError(e) from e

            results.extend(cached_data)
        elif use_cache is False:
            non_cached_urls = urls

        async def get_one(url):
            """Get the data for one URL."""
            data = await get_form_4_data(url)
            result = await parse_form_4_data(data)
            if not result and use_cache is True:
                df = DataFrame([{"filing_url": url}])
                df.to_sql("form4_data", conn, if_exists="append", index=False)

            if result:
                df = DataFrame(result)
                df["filing_url"] = url
                df = df.replace({nan: None}).rename(columns=field_map)
                try:
                    if use_cache is True:
                        df.to_sql("form4_data", conn, if_exists="append", index=False)
                except sqlite3.DatabaseError as e:
                    if "no column named" in str(e):
                        missing_column = (
                            str(e).split("no column named ")[1].split(" ")[0]
                        )
                        missing_column = field_map.get(missing_column, missing_column)
                        add_missing_column(conn, missing_column)
                        df.to_sql("form4_data", conn, if_exists="append", index=False)
                    else:
                        raise OpenBBError(e) from e
                results.extend(df.replace({nan: None}).to_dict(orient="records"))

        time_estimate = (len(non_cached_urls) / 7) * 1.8
        logger.info(
            "Found %d total filings and %d uncached entries to download, estimated download time: %d seconds.",
            len(urls),
            len(non_cached_urls),
            round(time_estimate),
        )
        min_warn_time = 10
        if time_estimate > min_warn_time:
            logger.info(
                "Warning: This function is not intended for mass data collection."
                " Long download times are due to limitations with concurrent downloads from the SEC."
                "\n\nReduce the number of requests by using a more specific date range."
            )

        if len(non_cached_urls) > 0:
            async with asyncio.Semaphore(8):
                for url_chunk in [
                    non_cached_urls[i : i + 8]
                    for i in range(0, len(non_cached_urls), 8)
                ]:
                    await asyncio.gather(*[get_one(url) for url in url_chunk])
                    await asyncio.sleep(1.125)

        if use_cache is True:
            close_db(conn, db_path)

        results = [entry for entry in results if entry.get("filing_date")]

        return sorted(results, key=lambda x: x["filing_date"], reverse=True)

    except Exception as e:  # pylint: disable=broad-except
        if use_cache is True:
            close_db(conn, db_path)
        raise OpenBBError(
            f"Unexpected error while downloading and processing data -> {e.__class__.__name__}: {e}"
        ) from e