def _set_list_header_if_not_empty(self, msg, header, values):
        """
        Set msg's header, either from self.extra_headers, if present, or from
        the values argument if not empty.
        """
        try:
            msg[header] = self.extra_headers[header]
        except KeyError:
            if values:
                msg[header] = ", ".join(str(v) for v in values)