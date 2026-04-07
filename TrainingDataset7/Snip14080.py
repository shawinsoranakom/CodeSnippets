def regex(self):
        # This is only used by reverse() and cached in _reverse_dict.
        return re.compile(re.escape(self.language_prefix))