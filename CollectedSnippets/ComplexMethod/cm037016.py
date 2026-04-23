def on_startup(command: Literal["build", "gh-deploy", "serve"], dirty: bool):
    # Monkey-patch dirname_to_title in awesome-nav so that sub-directory names are
    # title-cased (e.g. "Offline Inference" instead of "Offline inference").
    import mkdocs_awesome_nav.nav.directory as _nav_dir

    _nav_dir.dirname_to_title = title
    logger.info("Generating example documentation")
    logger.debug("Root directory: %s", ROOT_DIR.resolve())
    logger.debug("Example directory: %s", EXAMPLE_DIR.resolve())
    logger.debug("Example document directory: %s", EXAMPLE_DOC_DIR.resolve())

    # Create the EXAMPLE_DOC_DIR if it doesn't exist
    if not EXAMPLE_DOC_DIR.exists():
        EXAMPLE_DOC_DIR.mkdir(parents=True)

    categories = sorted(p for p in EXAMPLE_DIR.iterdir() if p.is_dir())

    examples = []
    glob_patterns = ["*.py", "*.md", "*.sh"]
    # Find categorised examples
    for category in categories:
        logger.info("Processing category: %s", category.stem)
        globs = [category.glob(pattern) for pattern in glob_patterns]
        for path in itertools.chain(*globs):
            examples.append(Example(path, category.stem))
        # Find examples in subdirectories
        globs = [category.glob(f"*/{pattern}") for pattern in glob_patterns]
        for path in itertools.chain(*globs):
            examples.append(Example(path.parent, category.stem))

    # Generate the example documentation
    for example in sorted(examples, key=lambda e: e.path.stem):
        example_name = f"{example.path.stem}.md"
        doc_path = EXAMPLE_DOC_DIR / example.category / example_name
        if not doc_path.parent.exists():
            doc_path.parent.mkdir(parents=True)
        # Specify encoding for building on Windows
        with open(doc_path, "w+", encoding="utf-8") as f:
            f.write(example.generate())
        logger.debug("Example generated: %s", doc_path.relative_to(ROOT_DIR))
    logger.info("Total examples generated: %d", len(examples))