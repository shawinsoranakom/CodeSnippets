def _check_engines(self, engines):
        return list(
            chain.from_iterable(
                e._check_for_template_tags_with_the_same_name() for e in engines
            )
        )