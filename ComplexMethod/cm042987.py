async def test_generate_scoring_report(self, seeder):
        """Generate a comprehensive report of BM25 scoring effectiveness."""
        queries = {
            "beginner": "match schedule",
            "advanced": "tactical analysis pressing",
            "api": "VAR decision explanation",
            "deployment": "fixture changes due to weather",
            "extraction": "expected goals statistics"
        }

        report = {
            "timestamp": datetime.now().isoformat(),
            "domain": TEST_DOMAIN,
            "results": {}
        }

        for category, query in queries.items():
            config = SeedingConfig(
                source="sitemap",
                extract_head=True,
                query=query,
                scoring_method="bm25",
                max_urls=10
            )

            results = await seeder.urls(TEST_DOMAIN, config)

            report["results"][category] = {
                "query": query,
                "total_results": len(results),
                "top_results": [
                    {
                        "url": r["url"],
                        "score": r["relevance_score"],
                        "title": r["head_data"].get("title", "")
                    }
                    for r in results[:3]
                ],
                "score_distribution": {
                    "min": min(r["relevance_score"] for r in results) if results else 0,
                    "max": max(r["relevance_score"] for r in results) if results else 0,
                    "avg": sum(r["relevance_score"] for r in results) / len(results) if results else 0
                }
            }

        # Print report
        print("\n" + "="*60)
        print("BM25 SCORING EFFECTIVENESS REPORT")
        print("="*60)
        print(f"Domain: {report['domain']}")
        print(f"Timestamp: {report['timestamp']}")
        print("\nResults by Category:")

        for category, data in report["results"].items():
            print(f"\n{category.upper()}: '{data['query']}'")
            print(f"  Total results: {data['total_results']}")
            print(f"  Score range: {data['score_distribution']['min']:.3f} - {data['score_distribution']['max']:.3f}")
            print(f"  Average score: {data['score_distribution']['avg']:.3f}")
            print("  Top matches:")
            for i, result in enumerate(data['top_results']):
                print(f"    {i+1}. [{result['score']:.3f}] {result['title']}")