def _normalize_news_item(item: dict, sym: str) -> dict | None:
            """Flatten the response."""
            if not isinstance(item, dict):
                return None

            content = item.get("content")
            if not isinstance(content, dict):
                return None

            title = content.get("title") or content.get("summary")
            # Prefer clickThroughUrl; fallback to canonicalUrl; fallback to previewUrl
            url = None
            ctu = content.get("clickThroughUrl")
            if isinstance(ctu, dict):
                url = ctu.get("url")
            if not url:
                can = content.get("canonicalUrl")
                if isinstance(can, dict):
                    url = can.get("url")
            if not url:
                url = content.get("previewUrl")

            date = content.get("pubDate") or content.get("displayTime")

            # Optional fields
            provider = content.get("provider")
            source = provider.get("displayName") if isinstance(provider, dict) else None
            summary = content.get("summary") or content.get("description") or ""

            # If CompanyNewsData requires these, don't emit invalid items
            if not (sym and title and url and date):
                return None

            # CompanyNewsData typically includes: symbol, title, url, date, summary/text
            # We include both "summary" and "text" to be resilient across schema variants.
            normalized: dict[str, Any] = {
                "symbol": sym,
                "title": title,
                "url": url,
                "date": date,
                "source": source,
            }
            # Only add if non-empty to avoid weird validation rules
            if summary:
                normalized["summary"] = summary
                normalized["text"] = summary

            # Keep an id if present (harmless if the model ignores it)
            if item.get("id"):
                normalized["id"] = item["id"]
            elif content.get("id"):
                normalized["id"] = content["id"]

            return normalized