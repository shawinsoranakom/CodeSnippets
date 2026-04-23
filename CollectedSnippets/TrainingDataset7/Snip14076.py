def check(self):
        warnings = [
            *self._check_pattern_startswith_slash(),
            *self._check_pattern_unmatched_angle_brackets(),
        ]
        route = self._route
        if "(?P<" in route or route.startswith("^") or route.endswith("$"):
            warnings.append(
                Warning(
                    "Your URL pattern {} has a route that contains '(?P<', begins "
                    "with a '^', or ends with a '$'. This was likely an oversight "
                    "when migrating to django.urls.path().".format(self.describe()),
                    id="2_0.W001",
                )
            )
        return warnings