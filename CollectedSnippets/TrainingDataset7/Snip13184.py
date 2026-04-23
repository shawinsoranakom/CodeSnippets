def _tag_re_split(self):
        for position in self._tag_re_split_positions():
            yield self.template_string[slice(*position)], position