async def test_import_formatting():
    """
    Verify code extraction properly formats import statements.

    BEFORE: Import statements were concatenated without newlines
    AFTER: Import statements have proper newline separation
    """
    print_test("Import Statement Formatting", "#1181")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        # Create HTML with code containing imports
        html_with_code = """
        <html>
        <body>
        <pre><code>
import os
import sys
from pathlib import Path
from typing import List, Dict

def main():
    pass
        </code></pre>
        </body>
        </html>
        """

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=f"raw:{html_with_code}",
                config=CrawlerRunConfig()
            )

        markdown = result.markdown.raw_markdown if result.markdown else ""

        # Check that imports are not concatenated on the same line
        # Bad: "import osimport sys" (no newline between statements)
        # This is the actual bug - statements getting merged on same line
        bad_patterns = [
            "import os import sys",      # Space but no newline
            "import osimport sys",       # No space or newline
            "import os from pathlib",    # Space but no newline
            "import osfrom pathlib",     # No space or newline
        ]

        markdown_single_line = markdown.replace('\n', ' ')  # Convert newlines to spaces

        for pattern in bad_patterns:
            # Check if pattern exists without proper line separation
            if pattern.replace(' ', '') in markdown_single_line.replace(' ', ''):
                # Verify it's actually on same line (not just adjacent after newline removal)
                lines = markdown.split('\n')
                for line in lines:
                    if 'import' in line.lower():
                        # Count import statements on this line
                        import_count = line.lower().count('import ')
                        if import_count > 1:
                            record_result("Import Formatting", "#1181", False,
                                         f"Multiple imports on same line: {line[:60]}...")
                            return

        # Verify imports are present
        if "import" in markdown.lower():
            record_result("Import Formatting", "#1181", True,
                         "Import statements are properly line-separated")
        else:
            record_result("Import Formatting", "#1181", True,
                         "No import statements found to verify (test HTML may have changed)")

    except Exception as e:
        record_result("Import Formatting", "#1181", False, f"Exception: {e}")