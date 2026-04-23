def process_gitblob_url(url: str) -> str:
    """Check url to see if it describes a GitHub Gist "blob" URL.

    If so, returns a new URL to get the "raw" script.
    If not, returns URL unchanged.
    """
    # Matches github.com and gist.github.com.  Will not match githubusercontent.com.
    # See this regex with explainer and sample text here: https://regexr.com/4odk3
    match = _GITBLOB_RE.match(url)
    if match:
        mdict = match.groupdict()
        # If it has "blob" in the url, replace this with "raw" and we're done.
        if mdict["blob_or_raw"] == "blob":
            return "{base}{account}raw{suffix}".format(**mdict)

        # If it is a "raw" url already, return untouched.
        if mdict["blob_or_raw"] == "raw":
            return url

        # It's a gist. Just tack "raw" on the end.
        return url + "/raw"

    return url