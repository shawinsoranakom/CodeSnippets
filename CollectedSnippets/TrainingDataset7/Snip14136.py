def extract(self, to_path):
        namelist = self._archive.namelist()
        leading = self.has_leading_dir(namelist)
        for name in namelist:
            data = self._archive.read(name)
            info = self._archive.getinfo(name)
            if leading:
                name = self.split_leading_dir(name)[1]
            if not name:
                continue
            filename = self.target_filename(to_path, name)
            if name.endswith(("/", "\\")):
                # A directory
                os.makedirs(filename, exist_ok=True)
            else:
                dirname = os.path.dirname(filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                with open(filename, "wb") as outfile:
                    outfile.write(data)
                # Convert ZipInfo.external_attr to mode
                mode = info.external_attr >> 16
                self._copy_permissions(mode, filename)