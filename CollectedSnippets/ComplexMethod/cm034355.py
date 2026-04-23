def _parse_packet_header(self, pkt: PktPointer, offset: int, pktlen: int) -> tuple[int | None, int, int]:
        """
        Parse a PGP packet header to get tag and packet length.
        Returns (tag, body_length, header_length) or (None, 0, 0) on error.

        Per RFC 9580 - Section 4.2: Packet Headers
        https://www.rfc-editor.org/rfc/rfc9580.html#name-packet-headers
        """
        if offset >= pktlen:
            return None, 0, 0

        tag_byte = pkt[offset]

        # Check if it's a new format packet (bit 6 set)
        if tag_byte & 0x40:
            # New format
            tag = tag_byte & 0x3f  # bits 0-5 are packet type ID
            offset += 1

            if offset >= pktlen:
                return None, 0, 0

            first_len_byte = pkt[offset]

            if first_len_byte < 192:
                # One-octet length
                return tag, first_len_byte, 2
            elif first_len_byte < 224:
                # Two-octet length
                if offset + 1 >= pktlen:
                    return None, 0, 0
                length = ((first_len_byte - 192) << 8) + pkt[offset + 1] + 192
                return tag, length, 3
            elif first_len_byte == 255:
                # Five-octet length
                if offset + 4 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 24) | (pkt[offset + 2] << 16) | \
                         (pkt[offset + 3] << 8) | pkt[offset + 4]
                return tag, length, 6
            else:
                # Partial body length (not supported here)
                return None, 0, 0
        else:
            # Old format
            tag = (tag_byte >> 2) & 0x0f
            length_type = tag_byte & 0x03

            if length_type == 0:
                # One-octet length
                if offset + 1 >= pktlen:
                    return None, 0, 0
                return tag, pkt[offset + 1], 2
            elif length_type == 1:
                # Two-octet length
                if offset + 2 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 8) | pkt[offset + 2]
                return tag, length, 3
            elif length_type == 2:
                # Four-octet length
                if offset + 4 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 24) | (pkt[offset + 2] << 16) | \
                         (pkt[offset + 3] << 8) | pkt[offset + 4]
                return tag, length, 5
            else:
                # Indeterminate length (not supported)
                return None, 0, 0