def _convert(self, value, record, validate):
        if value is None or value is False:
            return None

        if not validate or not self.sanitize:
            return value

        sanitize_vals = {
            'silent': True,
            'sanitize_tags': self.sanitize_tags,
            'sanitize_attributes': self.sanitize_attributes,
            'sanitize_style': self.sanitize_style,
            'sanitize_form': self.sanitize_form,
            'sanitize_conditional_comments': self.sanitize_conditional_comments,
            'output_method': self.sanitize_output_method,
            'strip_style': self.strip_style,
            'strip_classes': self.strip_classes
        }

        if self.sanitize_overridable:
            if record.env.user.has_group('base.group_sanitize_override'):
                return value

            original_value = record[self.name]
            if original_value:
                # Note that sanitize also normalize
                original_value_sanitized = html_sanitize(original_value, **sanitize_vals)
                original_value_normalized = html_normalize(original_value)

                if (
                    not original_value_sanitized  # sanitizer could empty it
                    or original_value_normalized != original_value_sanitized
                ):
                    # The field contains element(s) that would be removed if
                    # sanitized. It means that someone who was part of a group
                    # allowing to bypass the sanitation saved that field
                    # previously.

                    diff = unified_diff(
                        original_value_sanitized.splitlines(),
                        original_value_normalized.splitlines(),
                    )

                    with_colors = isinstance(logging.getLogger().handlers[0].formatter, ColoredFormatter)
                    diff_str = f'The field ({record._description}, {self.string}) will not be editable:\n'
                    for line in list(diff)[2:]:
                        if with_colors:
                            color = {'-': RED, '+': GREEN}.get(line[:1], DEFAULT)
                            diff_str += COLOR_PATTERN % (30 + color, 40 + DEFAULT, line.rstrip() + "\n")
                        else:
                            diff_str += line.rstrip() + '\n'
                    _logger.info(diff_str)

                    raise UserError(record.env._(
                        "The field value you're saving (%(model)s %(field)s) includes content that is "
                        "restricted for security reasons. It is possible that someone "
                        "with higher privileges previously modified it, and you are therefore "
                        "not able to modify it yourself while preserving the content.",
                        model=record._description, field=self.string,
                    ))

        return html_sanitize(value, **sanitize_vals)