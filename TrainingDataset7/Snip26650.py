def get_mtime(gzipped_string):
        with gzip.GzipFile(mode="rb", fileobj=BytesIO(gzipped_string)) as f:
            f.read()  # must read the data before accessing the header
            return f.mtime