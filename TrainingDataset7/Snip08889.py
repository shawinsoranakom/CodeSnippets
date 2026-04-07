def cleanup_url(url):
            tmp = url.rstrip("/")
            filename = tmp.split("/")[-1]
            if url.endswith("/"):
                display_url = tmp + "/"
            else:
                display_url = url
            return filename, display_url