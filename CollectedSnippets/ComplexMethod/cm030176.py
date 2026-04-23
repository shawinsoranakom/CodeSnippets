def _ensure_valid_message(self, msg):
        # Ensure the message conforms to our protocol.
        # If anything needs to be changed here for a patch release of Python,
        # the 'revision' in protocol_version() should be updated.
        match msg:
            case {"message": str(), "type": str()}:
                # Have the client show a message. The client chooses how to
                # format the message based on its type. The currently defined
                # types are "info" and "error". If a message has a type the
                # client doesn't recognize, it must be treated as "info".
                pass
            case {"help": str()}:
                # Have the client show the help for a given argument.
                pass
            case {"prompt": str(), "state": str()}:
                # Have the client display the given prompt and wait for a reply
                # from the user. If the client recognizes the state it may
                # enable mode-specific features like multi-line editing.
                # If it doesn't recognize the state it must prompt for a single
                # line only and send it directly to the server. A server won't
                # progress until it gets a "reply" or "signal" message, but can
                # process "complete" requests while waiting for the reply.
                pass
            case {
                "completions": list(completions)
            } if all(isinstance(c, str) for c in completions):
                # Return valid completions for a client's "complete" request.
                pass
            case {
                "command_list": list(command_list)
            } if all(isinstance(c, str) for c in command_list):
                # Report the list of legal PDB commands to the client.
                # Due to aliases this list is not static, but the client
                # needs to know it for multi-line editing.
                pass
            case _:
                raise AssertionError(
                    f"PDB message doesn't follow the schema! {msg}"
                )