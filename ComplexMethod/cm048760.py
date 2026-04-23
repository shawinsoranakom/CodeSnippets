def _message_log_repartition_lines(self, old_values_str, new_values_str):
        self.ensure_one()
        if not self.is_used:
            return

        old_line_values_dict = ast.literal_eval(old_values_str or '{}')
        new_line_values_dict = ast.literal_eval(new_values_str)

        # Categorize the lines that were added/removed/modified
        modified_lines = [
            (line, old_line_values_dict[line], new_line_values_dict[line])
            for line in old_line_values_dict.keys() & new_line_values_dict.keys()
        ]
        added_and_deleted_lines = [
            (line, self.env._('Removed'), old_line_values_dict[line])
            if line in old_line_values_dict
            else (line, self.env._('New'), new_line_values_dict[line])
            for line in old_line_values_dict.keys() ^ new_line_values_dict.keys()
        ]

        for (document_type, sequence), old_value, new_value in modified_lines:
            diff_keys = [key for key in old_value if old_value[key] != new_value[key]]
            if diff_keys:
                body = Markup("<b>{type}</b> {rep} {seq}:<ul class='mb-0 ps-4'>{changes}</ul>").format(
                    type=document_type.capitalize(),
                    rep=_('repartition line'),
                    seq=sequence,
                    changes=Markup().join(
                        [Markup("""
                            <li>
                                <span class='o-mail-Message-trackingOld me-1 px-1 text-muted fw-bold'>{old}</span>
                                <i class='o-mail-Message-trackingSeparator fa fa-long-arrow-right mx-1 text-600'/>
                                <span class='o-mail-Message-trackingNew me-1 fw-bold text-info'>{new}</span>
                                <span class='o-mail-Message-trackingField ms-1 fst-italic text-muted'>({diff})</span>
                            </li>
                        """).format(old=old_value[diff_key], new=new_value[diff_key], diff=diff_key)
                        for diff_key in diff_keys]
                    )
                )
                super()._message_log(body=body)

        for (document_type, sequence), operation, value in added_and_deleted_lines:
            body = Markup("<b>{op} {type}</b> {rep} {seq}:<ul class='mb-0 ps-4'>{changes}</ul>").format(
                op=operation,
                type=document_type.capitalize(),
                rep=_('repartition line'),
                seq=sequence,
                changes=Markup().join(
                    [Markup("""
                        <li>
                            <span class='o-mail-Message-trackingNew me-1 fw-bold text-info'>{value}</span>
                            <span class='o-mail-Message-trackingField ms-1 fst-italic text-muted'>({diff})</span>
                        </li>
                    """).format(value=value[key], diff=key)
                    for key in value]
                )
            )
            super()._message_log(body=body)
        return