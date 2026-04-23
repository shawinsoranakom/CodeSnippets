def list(self, path: str) -> list[str]:
        if not path or path == '/':
            path = ''
        elif not path.endswith('/'):
            path += '/'
        # The delimiter logic screens out directories, so we can't use it. :(
        # For example, given a structure:
        #   foo/bar/zap.txt
        #   foo/bar/bang.txt
        #   ping.txt
        # prefix=None, delimiter="/"   yields  ["ping.txt"]  # :(
        # prefix="foo", delimiter="/"  yields  []  # :(
        results: set[str] = set()
        prefix_len = len(path)
        response: ListObjectsV2OutputDict = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=path
        )
        contents = response.get('Contents')
        if not contents:
            return []
        paths = [obj['Key'] for obj in contents]
        for sub_path in paths:
            if sub_path == path:
                continue
            try:
                index = sub_path.index('/', prefix_len + 1)
                if index != prefix_len:
                    results.add(sub_path[: index + 1])
            except ValueError:
                results.add(sub_path)
        return list(results)