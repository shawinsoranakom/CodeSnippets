def main():
    """Build docs, update titles and edit links, minify HTML, and print local server command."""
    if not shutil.which("zensical"):
        raise SystemExit("zensical is not installed. Install it with: pip install -e '.[dev]'")

    start_time = time.perf_counter()
    backup_root: Path | None = None
    docs_backups: list[tuple[Path, Path]] = []
    restored = False

    def restore_all():
        """Restore docs sources from backup once build steps complete."""
        nonlocal restored
        if backup_root:
            LOGGER.info("Restoring docs directory from backup")
            restore_docs_sources(backup_root, docs_backups)
        restored = True

    try:
        backup_root, docs_backups = backup_docs_sources()
        prepare_docs_markdown()
        build_reference_docs(update_nav=False)
        render_jinja_macros()

        # Remove cloned repos before serving/building to keep the tree lean during mkdocs processing
        shutil.rmtree(DOCS / "repos", ignore_errors=True)

        # Build the main documentation
        LOGGER.info(f"Building docs from {DOCS}")
        subprocess.run(["zensical", "build", "-f", str(DOCS.parent / "mkdocs.yml"), "--strict"], check=True)
        LOGGER.info(f"Site built at {SITE}")

        # Remove search index JSON files to disable search
        Path(SITE / "search.json").unlink(missing_ok=True)

        # Update docs HTML pages
        update_docs_html()

        # Post-process site for meta tags, authors, social cards, and mkdocstrings polish
        if postprocess_site:
            postprocess_site(
                site_dir=SITE,
                docs_dir=DOCS / "en",
                site_url="https://docs.ultralytics.com",
                default_image="https://raw.githubusercontent.com/ultralytics/assets/main/yolov8/banner-yolov8.png",
                default_author="glenn.jocher@ultralytics.com",
                add_desc=False,
                add_image=True,
                add_authors=True,
                add_json_ld=True,
                add_share_buttons=True,
                add_css=False,
                verbose=True,
            )
        else:
            LOGGER.warning("postprocess_site not available; skipping mkdocstrings postprocessing")

        # Minify files
        minify_files(html=False, css=False, js=False)

        # Add missing pages to sitemap
        sitemap = SITE / "sitemap.xml"
        if sitemap.exists():
            content = sitemap.read_text()
            in_sitemap = set(re.findall(r"<loc>([^<]+)</loc>", content))
            all_pages = {
                f"https://docs.ultralytics.com/{f.relative_to(SITE).as_posix().replace('index.html', '')}"
                for f in SITE.rglob("*.html")
                if f.name != "404.html"
            }
            if missing := (all_pages - in_sitemap):
                entries = "\n".join(f"  <url>\n    <loc>{u}</loc>\n  </url>" for u in sorted(missing))
                sitemap.write_text(content.replace("</urlset>", f"{entries}\n</urlset>"))
            LOGGER.info(
                f"{len(all_pages)}/{len(all_pages)} pages in sitemap.xml ✅ (+{len(missing)} added)"
                if missing
                else f"{len(in_sitemap)}/{len(all_pages)} pages in sitemap.xml ✅"
            )

        # Print results and auto-serve on macOS
        size = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file()) >> 20
        duration = time.perf_counter() - start_time
        LOGGER.info(f"Docs built correctly ✅ ({size:.1f}MB, {duration:.1f}s)")

        # Restore sources before optionally serving
        restore_all()

        if (MACOS or LINUX) and not os.getenv("GITHUB_ACTIONS"):
            import webbrowser

            url = "http://localhost:8000"
            LOGGER.info(f"Opening browser at {url}")
            webbrowser.open(url)
            try:
                subprocess.run([sys.executable, "-m", "http.server", "--directory", str(SITE), "8000"], check=True)
            except KeyboardInterrupt:
                LOGGER.info(f"\n✅ Server stopped. Restart at {url}")
            except Exception as e:
                if "Address already in use" in str(e):
                    LOGGER.info("Port 8000 in use; skipping auto-serve. Serve manually if needed.")
                else:
                    LOGGER.info(f"\n❌ Server failed: {e}")
        else:
            LOGGER.info('Serve site at http://localhost:8000 with "python -m http.server --directory site"')
    finally:
        if not restored:
            restore_all()
        shutil.rmtree(DOCS / "repos", ignore_errors=True)