async def demo_security_analysis():
    """Using network capture for security analysis"""
    print("\n=== 5. Security Analysis with Network Capture ===")

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            capture_console_messages=True,
            wait_until="networkidle"
        )

        # A site that makes multiple third-party requests
        result = await crawler.arun(
            url="https://www.nytimes.com/",
            config=config
        )

        if result.success and result.network_requests:
            print(f"Captured {len(result.network_requests)} network events")

            # Extract all domains
            domains = set()
            for req in result.network_requests:
                if req.get("event_type") == "request":
                    url = req.get("url", "")
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        if domain:
                            domains.add(domain)
                    except:
                        pass

            print(f"\nDetected requests to {len(domains)} unique domains:")
            main_domain = urlparse(result.url).netloc

            # Separate first-party vs third-party domains
            first_party = [d for d in domains if main_domain in d]
            third_party = [d for d in domains if main_domain not in d]

            print(f"  - First-party domains: {len(first_party)}")
            print(f"  - Third-party domains: {len(third_party)}")

            # Look for potential trackers/analytics
            tracking_keywords = ["analytics", "tracker", "pixel", "tag", "stats", "metric", "collect", "beacon"]
            potential_trackers = []

            for domain in third_party:
                if any(keyword in domain.lower() for keyword in tracking_keywords):
                    potential_trackers.append(domain)

            if potential_trackers:
                print(f"\nPotential tracking/analytics domains ({len(potential_trackers)}):")
                for i, domain in enumerate(sorted(potential_trackers)[:10], 1):
                    print(f"  {i}. {domain}")
                if len(potential_trackers) > 10:
                    print(f"     ... and {len(potential_trackers) - 10} more")

            # Check for insecure (HTTP) requests
            insecure_requests = [
                req.get("url") for req in result.network_requests 
                if req.get("event_type") == "request" and req.get("url", "").startswith("http://")
            ]

            if insecure_requests:
                print(f"\nWarning: Found {len(insecure_requests)} insecure (HTTP) requests:")
                for i, url in enumerate(insecure_requests[:5], 1):
                    print(f"  {i}. {url}")
                if len(insecure_requests) > 5:
                    print(f"     ... and {len(insecure_requests) - 5} more")

            # Save security analysis to file
            output_file = os.path.join(__cur_dir__, "tmp", "security_analysis.json")
            with open(output_file, "w") as f:
                json.dump({
                    "url": result.url,
                    "main_domain": main_domain,
                    "timestamp": datetime.now().isoformat(),
                    "analysis": {
                        "total_requests": len([r for r in result.network_requests if r.get("event_type") == "request"]),
                        "unique_domains": len(domains),
                        "first_party_domains": first_party,
                        "third_party_domains": third_party,
                        "potential_trackers": potential_trackers,
                        "insecure_requests": insecure_requests
                    }
                }, f, indent=2)

            print(f"\nFull security analysis saved to {output_file}")