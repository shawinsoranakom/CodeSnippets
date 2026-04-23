def build(repo_root: Path) -> None:
    """Main build: parse README, render single-page HTML via Jinja2 templates."""
    website = repo_root / "website"
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")

    subtitle = ""
    for line in readme_text.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            subtitle = stripped
            break

    parsed_groups = parse_readme(readme_text)
    sponsors = parse_sponsors(readme_text)

    categories = [cat for g in parsed_groups for cat in g["categories"]]
    total_entries = sum(c["entry_count"] for c in categories)
    entries = extract_entries(categories, parsed_groups)

    stars_data = load_stars(website / "data" / "github_stars.json")

    repo_self = stars_data.get("vinta/awesome-python", {})
    repo_stars = None
    if "stars" in repo_self:
        stars_val = repo_self["stars"]
        repo_stars = f"{stars_val // 1000}k" if stars_val >= 1000 else str(stars_val)

    for entry in entries:
        repo_key = extract_github_repo(entry["url"])
        if not repo_key and entry.get("source_type") == "Built-in":
            repo_key = "python/cpython"
        if repo_key and repo_key in stars_data:
            sd = stars_data[repo_key]
            entry["stars"] = sd["stars"]
            entry["owner"] = sd["owner"]
            entry["last_commit_at"] = sd.get("last_commit_at", "")

    entries = sort_entries(entries)

    env = Environment(
        loader=FileSystemLoader(website / "templates"),
        autoescape=True,
    )

    site_dir = website / "output"
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True)

    tpl_index = env.get_template("index.html")
    (site_dir / "index.html").write_text(
        tpl_index.render(
            categories=categories,
            subtitle=subtitle,
            entries=entries,
            total_entries=total_entries,
            total_categories=len(categories),
            repo_stars=repo_stars,
            build_date=datetime.now(UTC).strftime("%B %d, %Y"),
            sponsors=sponsors,
        ),
        encoding="utf-8",
    )

    static_src = website / "static"
    static_dst = site_dir / "static"
    if static_src.exists():
        shutil.copytree(static_src, static_dst, dirs_exist_ok=True)

    (site_dir / "llms.txt").write_text(readme_text, encoding="utf-8")

    print(f"Built single page with {len(parsed_groups)} groups, {len(categories)} categories")
    print(f"Total entries: {total_entries}")
    print(f"Output: {site_dir}")