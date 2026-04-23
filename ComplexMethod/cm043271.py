def process_image(
        self, img: lhtml.HtmlElement, url: str, index: int, total_images: int, **kwargs
    ) -> Optional[List[Dict]]:
        # Quick validation checks
        style = img.get("style", "")
        alt = img.get("alt", "")
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        srcset = img.get("srcset", "")
        data_srcset = img.get("data-srcset", "")

        if "display:none" in style:
            return None

        parent = img.getparent()
        if parent.tag in ["button", "input"]:
            return None

        parent_classes = parent.get("class", "").split()
        if any(
            "button" in cls or "icon" in cls or "logo" in cls for cls in parent_classes
        ):
            return None

        # If src is in class or alt, likely an icon
        if (src and any(c in src for c in ["button", "icon", "logo"])) or (
            alt and any(c in alt for c in ["button", "icon", "logo"])
        ):
            return None

        # Score calculation
        score = 0
        if (width := img.get("width")) and width.isdigit():
            score += 1 if int(width) > 150 else 0
        if (height := img.get("height")) and height.isdigit():
            score += 1 if int(height) > 150 else 0
        if alt:
            score += 1
        score += index / total_images < 0.5

        # Check formats in all possible sources
        image_formats = {"jpg", "jpeg", "png", "webp", "avif", "gif"}
        detected_format = None
        for url in [src, data_src, srcset, data_srcset]:
            if url:
                format_matches = [fmt for fmt in image_formats if fmt in url.lower()]
                if format_matches:
                    detected_format = format_matches[0]
                    score += 1
                    break

        if srcset or data_srcset:
            score += 1

        if picture := img.xpath("./ancestor::picture[1]"):
            score += 1

        if score <= kwargs.get("image_score_threshold", IMAGE_SCORE_THRESHOLD):
            return None

        # Process image variants
        unique_urls = set()
        image_variants = []
        base_info = {
            "alt": alt,
            "desc": self.find_closest_parent_with_useful_text(img, **kwargs),
            "score": score,
            "type": "image",
            "group_id": index,
            "format": detected_format,
        }

        def add_variant(src: str, width: Optional[str] = None):
            if src and not src.startswith("data:") and src not in unique_urls:
                unique_urls.add(src)
                variant = {**base_info, "src": src}
                if width:
                    variant["width"] = width
                image_variants.append(variant)

        # Add variants from different sources
        add_variant(src)
        add_variant(data_src)

        for srcset_attr in [srcset, data_srcset]:
            if srcset_attr:
                for source in parse_srcset(srcset_attr):
                    add_variant(source["url"], source["width"])

        # Handle picture element
        if picture:
            for source in picture[0].xpath(".//source[@srcset]"):
                if source_srcset := source.get("srcset"):
                    for src_data in parse_srcset(source_srcset):
                        add_variant(src_data["url"], src_data["width"])

        # Check framework-specific attributes
        for attr, value in img.attrib.items():
            if (
                attr.startswith("data-")
                and ("src" in attr or "srcset" in attr)
                and "http" in value
            ):
                add_variant(value)

        return image_variants if image_variants else None