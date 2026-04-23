def process_payload(self, payload):
        match payload:
            case {
                "command_list": command_list
            } if all(isinstance(c, str) for c in command_list):
                self.pdb_commands = set(command_list)
            case {"message": str(msg), "type": str(msg_type)}:
                if msg_type == "error":
                    print("***", msg, flush=True)
                else:
                    print(msg, end="", flush=True)
            case {"help": str(arg)}:
                self.pdb_instance.do_help(arg)
            case {"prompt": str(prompt), "state": str(state)}:
                if state not in ("pdb", "interact"):
                    state = "dumb"
                self.state = state
                self.prompt_for_reply(prompt)
            case _:
                raise RuntimeError(f"Unrecognized payload {payload}")