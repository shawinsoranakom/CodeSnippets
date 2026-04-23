def onecmd(self, command: str) -> bool:
        try:
            result = self.parse_command(command)

            if isinstance(result, dict):
                if "type" in result and result.get("type") == "empty":
                    return False

            self.execute_command(result)

            if isinstance(result, Tree):
                return False

            if result.get("type") == "meta" and result.get("command") in ["q", "quit", "exit"]:
                return True

        except KeyboardInterrupt:
            print("\nUse '\\q' to quit")
        except EOFError:
            print("\nGoodbye!")
            return True
        return False