def extract(self, to_path):
        members = self._archive.getmembers()
        leading = self.has_leading_dir(x.name for x in members)
        for member in members:
            name = member.name
            if leading:
                name = self.split_leading_dir(name)[1]
            filename = self.target_filename(to_path, name)
            if member.isdir():
                if filename:
                    os.makedirs(filename, exist_ok=True)
            else:
                try:
                    extracted = self._archive.extractfile(member)
                except (KeyError, AttributeError) as exc:
                    # Some corrupt tar files seem to produce this
                    # (specifically bad symlinks)
                    print(
                        "In the tar file %s the member %s is invalid: %s"
                        % (name, member.name, exc)
                    )
                else:
                    dirname = os.path.dirname(filename)
                    if dirname:
                        os.makedirs(dirname, exist_ok=True)
                    with open(filename, "wb") as outfile:
                        shutil.copyfileobj(extracted, outfile)
                        self._copy_permissions(member.mode, filename)
                finally:
                    if extracted:
                        extracted.close()