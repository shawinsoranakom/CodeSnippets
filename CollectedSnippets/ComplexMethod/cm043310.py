def _extract_text_context(self, head_data: Dict[str, Any]) -> str:
        """Extract all relevant text from head metadata for scoring."""
        # Priority fields with their weights (for future enhancement)
        text_parts = []

        # Title
        if head_data.get("title"):
            text_parts.append(head_data["title"])

        # Standard meta tags
        meta = head_data.get("meta", {})
        for key in ["description", "keywords", "author", "subject", "summary", "abstract"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Open Graph tags
        for key in ["og:title", "og:description", "og:site_name", "article:tag"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Twitter Card tags
        for key in ["twitter:title", "twitter:description", "twitter:image:alt"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Dublin Core tags
        for key in ["dc.title", "dc.description", "dc.subject", "dc.creator"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # JSON-LD structured data
        for jsonld in head_data.get("jsonld", []):
            if isinstance(jsonld, dict):
                # Extract common fields from JSON-LD
                for field in ["name", "headline", "description", "abstract", "keywords"]:
                    if field in jsonld:
                        if isinstance(jsonld[field], str):
                            text_parts.append(jsonld[field])
                        elif isinstance(jsonld[field], list):
                            text_parts.extend(str(item)
                                              for item in jsonld[field] if item)

                # Handle @graph structures
                if "@graph" in jsonld and isinstance(jsonld["@graph"], list):
                    for item in jsonld["@graph"]:
                        if isinstance(item, dict):
                            for field in ["name", "headline", "description"]:
                                if field in item and isinstance(item[field], str):
                                    text_parts.append(item[field])

        # Combine all text parts
        return " ".join(filter(None, text_parts))