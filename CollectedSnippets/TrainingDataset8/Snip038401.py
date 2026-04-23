def select_subprotocol(self, subprotocols: List[str]) -> Optional[str]:
        """Return the first subprotocol in the given list.

        This method is used by Tornado to select a protocol when the
        Sec-WebSocket-Protocol header is set in an HTTP Upgrade request.

        NOTE: We repurpose the Sec-WebSocket-Protocol header here in a slightly
        unfortunate (but necessary) way. The browser WebSocket API doesn't allow us to
        set arbitrary HTTP headers, and this header is the only one where we have the
        ability to set it to arbitrary values, so we use it to pass an auth token from
        client to server as the *second* value in the list.

        The reason why the auth token is set as the second value is that, when
        Sec-WebSocket-Protocol is set, many clients expect the server to respond with a
        selected subprotocol to use. We don't want that reply to be the auth token, so
        we just hard-code it to "streamlit".
        """
        if subprotocols:
            return subprotocols[0]

        return None