def test_get_pages(tmpdir):
    # Write an empty string to create a file.
    tmpdir.join("streamlit_app.py").write("")

    pages_dir = tmpdir.mkdir("pages")
    pages = [
        # These pages are out of order so that we can check that they're sorted
        # in the assert below.
        "03_other_page.py",
        "04 last numbered page.py",
        "01-page.py",
        # This page should appear last since it doesn't have an integer prefix.
        "page.py",
        # This file shouldn't appear as a page because it's hidden.
        ".hidden_file.py",
        # This shouldn't appear because it's not a Python file.
        "not_a_page.rs",
    ]
    for p in pages:
        pages_dir.join(p).write("")

    main_script_path = str(tmpdir / "streamlit_app.py")

    received_pages = source_util.get_pages(main_script_path)
    assert received_pages == {
        calc_md5(main_script_path): {
            "page_script_hash": calc_md5(main_script_path),
            "page_name": "streamlit_app",
            "script_path": main_script_path,
            "icon": "",
        },
        calc_md5(str(pages_dir / "01-page.py")): {
            "page_script_hash": calc_md5(str(pages_dir / "01-page.py")),
            "page_name": "page",
            "script_path": str(pages_dir / "01-page.py"),
            "icon": "",
        },
        calc_md5(str(pages_dir / "03_other_page.py")): {
            "page_script_hash": calc_md5(str(pages_dir / "03_other_page.py")),
            "page_name": "other_page",
            "script_path": str(pages_dir / "03_other_page.py"),
            "icon": "",
        },
        calc_md5(str(pages_dir / "04 last numbered page.py")): {
            "page_script_hash": calc_md5(str(pages_dir / "04 last numbered page.py")),
            "page_name": "last_numbered_page",
            "script_path": str(pages_dir / "04 last numbered page.py"),
            "icon": "",
        },
        calc_md5(str(pages_dir / "page.py")): {
            "page_script_hash": calc_md5(str(pages_dir / "page.py")),
            "page_name": "page",
            "script_path": str(pages_dir / "page.py"),
            "icon": "",
        },
    }

    # Assert address-equality to verify the cache is used the second time
    # get_pages is called.
    assert source_util.get_pages(main_script_path) is received_pages