def __init__(self, filename):
        self.filename = filename
        abspath = os.path.abspath(filename)
        abs_ckpt_dir = os.path.abspath(shared.cmd_opts.ckpt_dir) if shared.cmd_opts.ckpt_dir is not None else None

        self.is_safetensors = os.path.splitext(filename)[1].lower() == ".safetensors"

        if abs_ckpt_dir and abspath.startswith(abs_ckpt_dir):
            name = abspath.replace(abs_ckpt_dir, '')
        elif abspath.startswith(model_path):
            name = abspath.replace(model_path, '')
        else:
            name = os.path.basename(filename)

        if name.startswith("\\") or name.startswith("/"):
            name = name[1:]

        def read_metadata():
            metadata = read_metadata_from_safetensors(filename)
            self.modelspec_thumbnail = metadata.pop('modelspec.thumbnail', None)

            return metadata

        self.metadata = {}
        if self.is_safetensors:
            try:
                self.metadata = cache.cached_data_for_file('safetensors-metadata', "checkpoint/" + name, filename, read_metadata)
            except Exception as e:
                errors.display(e, f"reading metadata for {filename}")

        self.name = name
        self.name_for_extra = os.path.splitext(os.path.basename(filename))[0]
        self.model_name = os.path.splitext(name.replace("/", "_").replace("\\", "_"))[0]
        self.hash = model_hash(filename)

        self.sha256 = hashes.sha256_from_cache(self.filename, f"checkpoint/{name}")
        self.shorthash = self.sha256[0:10] if self.sha256 else None

        self.title = name if self.shorthash is None else f'{name} [{self.shorthash}]'
        self.short_title = self.name_for_extra if self.shorthash is None else f'{self.name_for_extra} [{self.shorthash}]'

        self.ids = [self.hash, self.model_name, self.title, name, self.name_for_extra, f'{name} [{self.hash}]']
        if self.shorthash:
            self.ids += [self.shorthash, self.sha256, f'{self.name} [{self.shorthash}]', f'{self.name_for_extra} [{self.shorthash}]']