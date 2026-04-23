def __init__(self, url: str, use_cache: bool = True):
        """Initialize the Filing class."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import run_async
        from openbb_sec.utils.helpers import cik_map

        super().__init__()

        if not url:
            raise ValueError("Please enter a URL.")

        if "/data/" not in url:
            raise ValueError("Invalid SEC URL supplied, must be a filing URL.")

        check_val: str = url.split("/data/")[1].split("/")[1]

        if len(check_val) != 18:
            raise ValueError("Invalid SEC URL supplied, must be a filing URL.")

        new_url = url.split(check_val)[0] + check_val + "/"

        cik_check = new_url.split("/")[-3]
        new_url = new_url.replace(f"/{cik_check}/", f"/{cik_check.lstrip('0')}/")
        self._url = new_url
        self._use_cache = use_cache
        index_headers = (
            check_val[:-8]
            + "-"
            + check_val[-8:-6]
            + "-"
            + check_val[-6:]
            + "-index-headers.htm"
        )
        self._index_headers_url = self._url + index_headers
        self._download_index_headers()

        if self._document_urls:
            for doc in self._document_urls:
                if doc.get("url", "").endswith("R1.htm"):
                    self._cover_page_url = doc.get("url")
                    break

        if self.has_cover_page and not self._cover_page:
            self._download_cover_page()

        if not self._trading_symbols:
            symbol = run_async(cik_map, self._cik)
            if symbol:
                self._trading_symbols = [symbol]