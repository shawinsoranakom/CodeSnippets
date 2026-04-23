def copy(self, default=None):
        default = default or {}
        copy_attachments = 'attachment_ids' not in default
        if copy_attachments:
            default['attachment_ids'] = False
        copies = super().copy(default=default)

        if copy_attachments:
            for copy, original in zip(copies, self):
                # copy attachments, to avoid ownership / ACLs issue
                # anyway filestore should keep a single reference to content
                if original.attachment_ids:
                    copy.write({
                        'attachment_ids': [
                            (4, att_copy.id) for att_copy in (
                                attachment.copy(default={'res_id': copy.id, 'res_model': original._name}) for attachment in original.attachment_ids
                            )
                        ]
                    })
        return copies