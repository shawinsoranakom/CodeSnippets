def get_street_view(address: str) -> str:
    """Capture Google Street View images of a location (4 angles: N/E/S/W).

    Returns image metadata. Images are stored in Streamlit session state and displayed after the investigation.

    Args:
        address: Street address to photograph
    """
    if not address:
        return json.dumps({"status": "error", "error": "address is required"})

    api_key = _google_key()
    if not api_key:
        return json.dumps({
            "status": "no_key",
            "address": address,
            "note": "No Google Maps API key. Street View unavailable.",
        })

    headings = [0, 90, 180, 270]
    images = []
    try:
        for heading in headings:
            params = {
                "location": address,
                "heading": heading,
                "size": "640x480",
                "key": api_key,
            }
            # Check metadata first
            meta_r = requests.get(
                "https://maps.googleapis.com/maps/api/streetview/metadata",
                params={**params, "return_error_codes": True},
                timeout=TOOL_TIMEOUT,
            )
            meta = meta_r.json()
            meta_status = meta.get("status", "").upper()
            if meta_status == "REQUEST_DENIED":
                return json.dumps({"status": "error", "error": meta.get("error_message", "Street View denied")})
            if meta_status != "OK":
                # ZERO_RESULTS = no imagery at this location; skip this heading
                continue

            img_r = requests.get(
                "https://maps.googleapis.com/maps/api/streetview",
                params=params,
                timeout=TOOL_TIMEOUT,
            )
            img_r.raise_for_status()
            images.append({
                "heading": heading,
                "capture_date": meta.get("date", "unknown"),
                "status": meta_status,
                "image_bytes": img_r.content,
            })

        if not images:
            return json.dumps({"status": "no_imagery", "address": address, "note": "No Street View imagery available for this address."})

        # Store raw image bytes in session state for Streamlit display.
        # Return only metadata to the LLM (base64 blobs are opaque text to the model
        # and would consume megabytes of context for a 10-provider investigation).
        cache = st.session_state.setdefault("street_view_cache", {})
        cache[address] = [
            {"heading": img["heading"], "capture_date": img["capture_date"], "image_bytes": img["image_bytes"]}
            for img in images
        ]

        return json.dumps({
            "status": "ok",
            "address": address,
            "images_captured": len(images),
            "capture_date": images[0].get("capture_date", "unknown"),
            "note": "Street View images captured. They will be displayed in the Surelock UI below the investigation narration.",
        })
    except Exception as exc:
        return json.dumps({"status": "error", "address": address, "error": str(exc)})