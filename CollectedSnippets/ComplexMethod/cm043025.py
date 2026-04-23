def deep_compare_links(self, old_links: Dict, new_links: Dict) -> List[str]:
        """Detailed comparison of link structures"""
        differences = []

        for category in ["internal", "external"]:
            old_urls = {link["href"] for link in old_links[category]}
            new_urls = {link["href"] for link in new_links[category]}

            missing = old_urls - new_urls
            extra = new_urls - old_urls

            if missing:
                differences.append(f"Missing {category} links: {missing}")
            if extra:
                differences.append(f"Extra {category} links: {extra}")

            # Compare link attributes for common URLs
            common = old_urls & new_urls
            for url in common:
                old_link = next(l for l in old_links[category] if l["href"] == url)
                new_link = next(l for l in new_links[category] if l["href"] == url)

                for attr in ["text", "title"]:
                    if old_link[attr] != new_link[attr]:
                        differences.append(
                            f"Link attribute mismatch for {url} - {attr}:"
                            f" old='{old_link[attr]}' vs new='{new_link[attr]}'"
                        )

        return differences