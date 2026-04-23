def as_divs(self):
                if not self:
                    return ""
                return mark_safe(
                    '<div class="error">%s</div>'
                    % "".join("<p>%s</p>" % e for e in self)
                )