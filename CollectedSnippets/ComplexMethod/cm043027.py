def run_tests(self) -> Dict:
        """Run comparison tests using the complicated HTML with multiple parameter scenarios."""
        # We'll still keep some "test_cases" logic from above (basic, complex, malformed).
        # But we add a new section for the complicated HTML scenarios.

        results = {"tests": [], "summary": {"passed": 0, "failed": 0}}

        # 1) First, run the existing 3 built-in test cases (basic, complex, malformed).
        # for case_name, html in self.test_cases.items():
        #     print(f"\nTesting built-in case: {case_name}...")

        #     original = WebScrapingStrategy()
        #     lxml = LXMLWebScrapingStrategy()

        #     start = time.time()
        #     orig_result = original.scrap("http://test.com", html)
        #     orig_time = time.time() - start

        #     print("\nOriginal Mode:")
        #     print(f"Cleaned HTML size: {len(orig_result['cleaned_html'])/1024:.2f} KB")
        #     print(f"Images: {len(orig_result['media']['images'])}")
        #     print(f"External links: {len(orig_result['links']['external'])}")
        #     print(f"Times - Original: {orig_time:.3f}s")

        #     start = time.time()
        #     lxml_result = lxml.scrap("http://test.com", html)
        #     lxml_time = time.time() - start

        #     print("\nLXML Mode:")
        #     print(f"Cleaned HTML size: {len(lxml_result['cleaned_html'])/1024:.2f} KB")
        #     print(f"Images: {len(lxml_result['media']['images'])}")
        #     print(f"External links: {len(lxml_result['links']['external'])}")
        #     print(f"Times - LXML: {lxml_time:.3f}s")

        #     # Compare
        #     diffs = {}
        #     link_diff = self.deep_compare_links(orig_result['links'], lxml_result['links'])
        #     if link_diff:
        #         diffs['links'] = link_diff

        #     media_diff = self.deep_compare_media(orig_result['media'], lxml_result['media'])
        #     if media_diff:
        #         diffs['media'] = media_diff

        #     html_diff = self.compare_html_content(orig_result['cleaned_html'], lxml_result['cleaned_html'])
        #     if html_diff:
        #         diffs['html'] = html_diff

        #     test_result = {
        #         'case': case_name,
        #         'lxml_mode': {
        #             'differences': diffs,
        #             'execution_time': lxml_time
        #         },
        #         'original_time': orig_time
        #     }
        #     results['tests'].append(test_result)

        #     if not diffs:
        #         results['summary']['passed'] += 1
        #     else:
        #         results['summary']['failed'] += 1

        # 2) Now, run the complicated HTML with multiple parameter scenarios.
        complicated_html = generate_complicated_html()
        print("\n=== Testing complicated HTML with multiple parameter scenarios ===")

        # Create the scrapers once (or you can re-create if needed)
        original = WebScrapingStrategy()
        lxml = LXMLWebScrapingStrategy()

        for scenario_name, params in get_test_scenarios().items():
            print(f"\nScenario: {scenario_name}")

            start = time.time()
            orig_result = original.scrap("http://test.com", complicated_html, **params)
            orig_time = time.time() - start

            start = time.time()
            lxml_result = lxml.scrap("http://test.com", complicated_html, **params)
            lxml_time = time.time() - start

            diffs = {}
            link_diff = self.deep_compare_links(
                orig_result["links"], lxml_result["links"]
            )
            if link_diff:
                diffs["links"] = link_diff

            media_diff = self.deep_compare_media(
                orig_result["media"], lxml_result["media"]
            )
            if media_diff:
                diffs["media"] = media_diff

            html_diff = self.compare_html_content(
                orig_result["cleaned_html"], lxml_result["cleaned_html"]
            )
            if html_diff:
                diffs["html"] = html_diff

            test_result = {
                "case": f"complicated_{scenario_name}",
                "lxml_mode": {"differences": diffs, "execution_time": lxml_time},
                "original_time": orig_time,
            }
            results["tests"].append(test_result)

            if not diffs:
                results["summary"]["passed"] += 1
                print(
                    f"✅ [OK] No differences found. Time(Orig: {orig_time:.3f}s, LXML: {lxml_time:.3f}s)"
                )
            else:
                results["summary"]["failed"] += 1
                print("❌ Differences found:")
                for category, dlist in diffs.items():
                    print(f"  {category}:")
                    for d in dlist:
                        print(f"    - {d}")

        return results