def categories(self):
        if not os.path.exists(self.content_dir):
            download_default_clip_interrogate_categories(self.content_dir)

        if self.loaded_categories is not None and self.skip_categories == shared.opts.interrogate_clip_skip_categories:
           return self.loaded_categories

        self.loaded_categories = []

        if os.path.exists(self.content_dir):
            self.skip_categories = shared.opts.interrogate_clip_skip_categories
            category_types = []
            for filename in Path(self.content_dir).glob('*.txt'):
                category_types.append(filename.stem)
                if filename.stem in self.skip_categories:
                    continue
                m = re_topn.search(filename.stem)
                topn = 1 if m is None else int(m.group(1))
                with open(filename, "r", encoding="utf8") as file:
                    lines = [x.strip() for x in file.readlines()]

                self.loaded_categories.append(Category(name=filename.stem, topn=topn, items=lines))

        return self.loaded_categories