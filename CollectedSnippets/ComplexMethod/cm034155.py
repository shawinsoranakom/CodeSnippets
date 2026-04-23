def evaluate_tags(self, only_tags, skip_tags, all_vars):
        """Check if the current item should be executed depending on the specified tags.

        NOTE this method is assumed to be called only on Task objects.
        """
        if self.tags:
            templar = TemplateEngine(loader=self._loader, variables=all_vars)
            for obj in self._get_all_taggable_objects():
                if (_tags := getattr(obj, "_tags", Sentinel)) is not Sentinel:
                    obj._tags = _flatten_tags(templar.template(_tags))
            tags = set(self.tags)
        else:
            # this makes isdisjoint work for untagged
            tags = self.untagged

        should_run = True  # default, tasks to run

        if only_tags:
            if 'always' in tags:
                should_run = True
            elif ('all' in only_tags and 'never' not in tags):
                should_run = True
            elif not tags.isdisjoint(only_tags):
                should_run = True
            elif 'tagged' in only_tags and tags != self.untagged and 'never' not in tags:
                should_run = True
            else:
                should_run = False

        if should_run and skip_tags:

            # Check for tags that we need to skip
            if 'all' in skip_tags:
                if 'always' not in tags or 'always' in skip_tags:
                    should_run = False
            elif not tags.isdisjoint(skip_tags):
                should_run = False
            elif 'tagged' in skip_tags and tags != self.untagged:
                should_run = False

        return should_run