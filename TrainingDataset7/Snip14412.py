def __init__(self, url, length, mime_type):
        "All args are expected to be strings"
        self.length, self.mime_type = length, mime_type
        self.url = iri_to_uri(url)