def iter_attachments(self):
        """Return an iterator over the non-main parts of a multipart.

        Skip the first of each occurrence of text/plain, text/html,
        multipart/related, or multipart/alternative in the multipart (unless
        they have a 'Content-Disposition: attachment' header) and include all
        remaining subparts in the returned iterator.  When applied to a
        multipart/related, return all parts except the root part.  Return an
        empty iterator when applied to a multipart/alternative or a
        non-multipart.
        """
        maintype, subtype = self.get_content_type().split('/')
        if maintype != 'multipart' or subtype == 'alternative':
            return
        payload = self.get_payload()
        # Certain malformed messages can have content type set to `multipart/*`
        # but still have single part body, in which case payload.copy() can
        # fail with AttributeError.
        try:
            parts = payload.copy()
        except AttributeError:
            # payload is not a list, it is most probably a string.
            return

        if maintype == 'multipart' and subtype == 'related':
            # For related, we treat everything but the root as an attachment.
            # The root may be indicated by 'start'; if there's no start or we
            # can't find the named start, treat the first subpart as the root.
            start = self.get_param('start')
            if start:
                found = False
                attachments = []
                for part in parts:
                    if part.get('content-id') == start:
                        found = True
                    else:
                        attachments.append(part)
                if found:
                    yield from attachments
                    return
            parts.pop(0)
            yield from parts
            return
        # Otherwise we more or less invert the remaining logic in get_body.
        # This only really works in edge cases (ex: non-text related or
        # alternatives) if the sending agent sets content-disposition.
        seen = []   # Only skip the first example of each candidate type.
        for part in parts:
            maintype, subtype = part.get_content_type().split('/')
            if ((maintype, subtype) in self._body_types and
                    not part.is_attachment() and subtype not in seen):
                seen.append(subtype)
                continue
            yield part