def save_content(content, media: Optional[MediaResponse], filepath: str, allowed_types=None) -> bool:
    if media:
        for url in media.get_list():
            if url.startswith(("http://", "https://")):
                try:
                    resp = requests.get(url, cookies=media.get("cookies"), headers=media.get("headers"))
                    if resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
                        return True
                except Exception as e:
                    print(f"Error fetching media '{url}': {e}", file=sys.stderr)
                return False
            else:
                content = url
                break
    if hasattr(content, "data"):
        content = content.data
    if not content:
        print("\nNo content to save.", file=sys.stderr)
        return False
    if content.startswith("data:"):
        with open(filepath, "wb") as f:
            f.write(extract_data_uri(content))
        return True
    if content.startswith("/media/"):
        src = content.replace("/media", get_media_dir()).split("?")[0]
        os.rename(src, filepath)
        return True
    filtered = filter_markdown(content, allowed_types)
    if filtered:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(filtered)
        return True
    print("\nUnable to save content.", file=sys.stderr)
    return False