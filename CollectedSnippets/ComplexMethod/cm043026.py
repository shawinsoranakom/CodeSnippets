def deep_compare_media(self, old_media: Dict, new_media: Dict) -> List[str]:
        """Detailed comparison of media elements"""
        differences = []

        for media_type in ["images", "videos", "audios"]:
            old_srcs = {item["src"] for item in old_media[media_type]}
            new_srcs = {item["src"] for item in new_media[media_type]}

            missing = old_srcs - new_srcs
            extra = new_srcs - old_srcs

            if missing:
                differences.append(f"Missing {media_type}: {missing}")
            if extra:
                differences.append(f"Extra {media_type}: {extra}")

            # Compare media attributes for common sources
            common = old_srcs & new_srcs
            for src in common:
                old_item = next(m for m in old_media[media_type] if m["src"] == src)
                new_item = next(m for m in new_media[media_type] if m["src"] == src)

                for attr in ["alt", "description"]:
                    if old_item.get(attr) != new_item.get(attr):
                        differences.append(
                            f"{media_type} attribute mismatch for {src} - {attr}:"
                            f" old='{old_item.get(attr)}' vs new='{new_item.get(attr)}'"
                        )

        return differences