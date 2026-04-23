def _sanitize_vals(self, vals):
        """Normalize the create/write values."""
        sanitized = vals.copy()

        # Wrap plain text in <div> if description has no HTML tags to avoid the padding with automatically added <p>
        if sanitized.get('description') and not re.search(r'<[^>]+>', sanitized['description']):
            sanitized['description'] = f"<div>{sanitized['description']}</div>"

        # Allow to provide invoice_repartition_line_ids and refund_repartition_line_ids by dispatching them
        # correctly in the repartition_line_ids
        if 'repartition_line_ids' in sanitized and (
            'invoice_repartition_line_ids' in sanitized
            or 'refund_repartition_line_ids' in sanitized
        ):
            del sanitized['repartition_line_ids']
        for doc_type in ('invoice', 'refund'):
            fname = f"{doc_type}_repartition_line_ids"
            if fname in sanitized:
                repartition = sanitized.setdefault('repartition_line_ids', [])
                for command_vals in sanitized.pop(fname):
                    if command_vals[0] == Command.CREATE:
                        repartition.append(Command.create({'document_type': doc_type, **command_vals[2]}))
                    elif command_vals[0] == Command.UPDATE:
                        repartition.append(Command.update(command_vals[1], {'document_type': doc_type, **command_vals[2]}))
                    else:
                        repartition.append(command_vals)
                sanitized[fname] = []
        return sanitized