def _check_pattern_unmatched_angle_brackets(self):
        warnings = []
        msg = "Your URL pattern %s has an unmatched '%s' bracket."
        brackets = re.findall(r"[<>]", str(self._route))
        open_bracket_counter = 0
        for bracket in brackets:
            if bracket == "<":
                open_bracket_counter += 1
            elif bracket == ">":
                open_bracket_counter -= 1
                if open_bracket_counter < 0:
                    warnings.append(
                        Warning(msg % (self.describe(), ">"), id="urls.W010")
                    )
                    open_bracket_counter = 0
        if open_bracket_counter > 0:
            warnings.append(Warning(msg % (self.describe(), "<"), id="urls.W010"))
        return warnings