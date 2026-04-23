def resolve(self, path=None, create=False, follow_symlinks=True):
        """
        Traverse zip hierarchy (parents, children and symlinks) starting
        from this PathInfo. This is called from three places:

        - When a zip file member is added to ZipFile.filelist, this method
          populates the ZipPathInfo tree (using create=True).
        - When ReadableZipPath.info is accessed, this method is finds a
          ZipPathInfo entry for the path without resolving any final symlink
          (using follow_symlinks=False)
        - When ZipPathInfo methods are called with follow_symlinks=True, this
          method resolves any symlink in the final path position.
        """
        link_count = 0
        stack = path.split('/')[::-1] if path else []
        info = self
        while True:
            if info.is_symlink() and (follow_symlinks or stack):
                link_count += 1
                if link_count >= 40:
                    return missing_zip_path_info  # Symlink loop!
                path = info.zip_file.read(info.zip_info).decode()
                stack += path.split('/')[::-1] if path else []
                info = info.parent

            if stack:
                name = stack.pop()
            else:
                return info

            if name == '..':
                info = info.parent
            elif name and name != '.':
                if name not in info.children:
                    if create:
                        info.children[name] = ZipPathInfo(info.zip_file, info)
                    else:
                        return missing_zip_path_info  # No such child!
                info = info.children[name]