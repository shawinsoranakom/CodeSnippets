async def async_main(opts):
    # ─────────── logging setup ───────────
    console = Console()
    logging.basicConfig(
        level=opts.log_level.upper(),
        format="%(message)s",
        handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
    )

    # -------------------------------------------------------------------
    # Load or build schemas (one‑time LLM call each)
    # -------------------------------------------------------------------
    company_schema = _load_or_build_schema(
        COMPANY_SCHEMA_PATH,
        _SAMPLE_COMPANY_HTML,
        _COMPANY_SCHEMA_QUERY,
        _COMPANY_SCHEMA_EXAMPLE,
        # True
    )
    people_schema = _load_or_build_schema(
        PEOPLE_SCHEMA_PATH,
        _SAMPLE_PEOPLE_HTML,
        _PEOPLE_SCHEMA_QUERY,
        _PEOPLE_SCHEMA_EXAMPLE,
        # True
    )

    outdir = BASE_DIR / pathlib.Path(opts.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    f_companies = (BASE_DIR / outdir / "companies.jsonl").open("a", encoding="utf-8")
    f_people = (BASE_DIR / outdir / "people.jsonl").open("a", encoding="utf-8")

    # -------------------------------------------------------------------
    # Prepare crawler with cookie pool rotation
    # -------------------------------------------------------------------
    profiler = BrowserProfiler()
    path = profiler.get_profile_path(opts.profile_name)
    bc = BrowserConfig(
        headless=False,        
        verbose=False,
        user_data_dir=path,
        use_managed_browser=True,
        user_agent_mode = "random",
        user_agent_generator_config= {
            "platforms": "mobile",
            "os": "Android"
        }
    )
    crawler = AsyncWebCrawler(config=bc)

    await crawler.start()

    # Single worker for simplicity; concurrency can be scaled by arun_many if needed.
    # crawler = await next_crawler().start()
    try:
        # Build LinkedIn search URL
        search_url = f'https://www.linkedin.com/search/results/companies/?keywords={quote(opts.query)}&companyHqGeo="{opts.geo}"'
        logging.info("Seed URL => %s", search_url)

        companies: List[Dict] = []
        if opts.cmd in ("companies", "full"):
            companies = await crawl_company_search(
                crawler, search_url, company_schema, opts.max_companies
            )
            for c in companies:
                f_companies.write(json.dumps(c, ensure_ascii=False) + "\n")
            logging.info(f"[bold green]✓[/] Companies scraped so far: {len(companies)}")

        if opts.cmd in ("people", "full"):
            if not companies:
                # load from previous run
                src = outdir / "companies.jsonl"
                if not src.exists():
                    logging.error("companies.jsonl missing — run companies/full first")
                    return 10
                companies = [json.loads(l) for l in src.read_text().splitlines()]
            total_people = 0
            title_kw = " ".join([t.strip() for t in opts.title_filters.split(",") if t.strip()]) if opts.title_filters else ""
            for comp in companies:
                people = await crawl_people_page(
                    crawler,
                    comp["people_url"],
                    people_schema,
                    opts.max_people,
                    title_kw,
                )
                for p in people:
                    rec = p | {
                        "company_handle": comp["handle"],
                        # "captured_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
                        "captured_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
                    }
                    f_people.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total_people += len(people)
                logging.info(
                    f"{comp['name']} — [cyan]{len(people)}[/] people extracted"
                )
                await asyncio.sleep(random.uniform(0.5, 1))
            logging.info("Total people scraped: %d", total_people)
    finally:
        await crawler.close()
        f_companies.close()
        f_people.close()

    return 0