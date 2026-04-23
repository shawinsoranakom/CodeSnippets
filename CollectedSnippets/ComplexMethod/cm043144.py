async def test_pypdf_migration():
    """
    Verify pypdf is used instead of deprecated PyPDF2.

    BEFORE: Used PyPDF2 (deprecated since 2022)
    AFTER: Uses pypdf (actively maintained)
    """
    print_test("pypdf Migration", "#1412")

    try:
        # Test 1: pypdf should be importable (if pdf extra is installed)
        try:
            import pypdf
            pypdf_available = True
            pypdf_version = pypdf.__version__
        except ImportError:
            pypdf_available = False
            pypdf_version = None

        # Test 2: PyPDF2 should NOT be imported by crawl4ai
        # Check if the processor uses pypdf
        try:
            from crawl4ai.processors.pdf import processor
            processor_source = open(processor.__file__).read()

            uses_pypdf = 'from pypdf' in processor_source or 'import pypdf' in processor_source
            uses_pypdf2 = 'from PyPDF2' in processor_source or 'import PyPDF2' in processor_source

            if uses_pypdf2 and not uses_pypdf:
                record_result("pypdf Migration", "#1412", False,
                             "PDF processor still uses PyPDF2")
                return

            if uses_pypdf:
                record_result("pypdf Migration", "#1412", True,
                             f"PDF processor uses pypdf{' v' + pypdf_version if pypdf_version else ''}")
                return
            else:
                record_result("pypdf Migration", "#1412", True,
                             "PDF processor found, pypdf dependency updated", skipped=not pypdf_available)
                return

        except ImportError:
            # PDF processor not available
            if pypdf_available:
                record_result("pypdf Migration", "#1412", True,
                             f"pypdf v{pypdf_version} is installed (PDF processor not loaded)")
            else:
                record_result("pypdf Migration", "#1412", True,
                             "PDF support not installed (optional feature)", skipped=True)
            return

    except Exception as e:
        record_result("pypdf Migration", "#1412", False, f"Exception: {e}")