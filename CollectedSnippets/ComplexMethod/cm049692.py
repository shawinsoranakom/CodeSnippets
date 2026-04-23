def write(self, vals):
        rec_db_contents = {}
        if 'html_field_history' in vals:
            del vals['html_field_history']
        versioned_fields = self._get_versioned_fields()
        vals_contain_versioned_fields = set(vals).intersection(versioned_fields)

        if vals_contain_versioned_fields:
            for rec in self:
                rec_db_contents[rec.id] = {f: rec[f] for f in versioned_fields}

        # Call super().write before generating the patch to be sure we perform
        # the diff on sanitized data
        write_result = super().write(vals)

        if not vals_contain_versioned_fields:
            return write_result

        # allow mutlti record write
        for rec in self:
            new_revisions = False
            fields_data = self.env[rec._name]._fields

            if any(f in vals and not fields_data[f].sanitize for f in versioned_fields):
                raise ValidationError(  # pylint: disable=missing-gettext
                    "Ensure all versioned fields ( %s ) in model %s are declared as sanitize=True"
                    % (str(versioned_fields), rec._name)
                )

            history_revs = rec.html_field_history or {}

            for field in versioned_fields:
                new_content = rec[field] or ""

                if field not in history_revs:
                    history_revs[field] = []

                old_content = rec_db_contents[rec.id][field] or ""
                if new_content != old_content:
                    new_revisions = True
                    patch = generate_patch(new_content, old_content)
                    revision_id = (
                        (history_revs[field][0]["revision_id"] + 1)
                        if history_revs[field]
                        else 1
                    )

                    history_revs[field].insert(
                        0,
                        {
                            "patch": patch,
                            "revision_id": revision_id,
                            "create_date": self.env.cr.now().isoformat(),
                            "create_uid": self.env.uid,
                            "create_user_name": self.env.user.name,
                        },
                    )
                    limit = rec._html_field_history_size_limit
                    history_revs[field] = history_revs[field][:limit]
            # Call super().write again to include the new revision
            if new_revisions:
                extra_vals = {"html_field_history": history_revs}
                write_result = super(HtmlFieldHistoryMixin, rec).write(extra_vals) and write_result

        return write_result