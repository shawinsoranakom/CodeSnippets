def parse_connection_args(self, args: List[str]) -> Dict[str, Any]:
        parser = argparse.ArgumentParser(description="RAGFlow CLI Client", add_help=False)
        parser.add_argument("-h", "--host", default="127.0.0.1", help="Admin or RAGFlow service host")
        parser.add_argument("-p", "--port", type=int, default=9381, help="Admin or RAGFlow service port")
        parser.add_argument("-w", "--password", default="admin", type=str, help="Superuser password")
        parser.add_argument("-t", "--type", default="admin", type=str, help="CLI mode, admin or user")
        parser.add_argument("-u", "--username", default=None,
                            help="Username (email). In admin mode defaults to admin@ragflow.io, in user mode required.")
        parser.add_argument("command", nargs="?", help="Single command")
        try:
            parsed_args, remaining_args = parser.parse_known_args(args)
            # Determine username based on mode
            username = parsed_args.username
            if parsed_args.type == "admin":
                if username is None:
                    username = "admin@ragflow.io"

            if remaining_args:
                if remaining_args[0] == "command":
                    command_str = ' '.join(remaining_args[1:]) + ';'
                    auth = True
                    if remaining_args[1] == "register":
                        auth = False
                    else:
                        if username is None:
                            print("Error: username (-u) is required in user mode")
                            return {"error": "Username required"}
                    return {
                        "host": parsed_args.host,
                        "port": parsed_args.port,
                        "password": parsed_args.password,
                        "type": parsed_args.type,
                        "username": username,
                        "command": command_str,
                        "auth": auth
                    }
                else:
                    return {"error": "Invalid command"}
            else:
                auth = True
                if username is None:
                    auth = False
                return {
                    "host": parsed_args.host,
                    "port": parsed_args.port,
                    "type": parsed_args.type,
                    "username": username,
                    "auth": auth
                }
        except SystemExit:
            return {"error": "Invalid connection arguments"}