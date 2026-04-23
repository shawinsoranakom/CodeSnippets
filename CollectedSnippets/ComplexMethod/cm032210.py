def run(self):
        print("NLTK Downloader")
        while True:
            self._simple_interactive_menu(
                "d) Download",
                "l) List",
                " u) Update",
                "c) Config",
                "h) Help",
                "q) Quit",
            )
            user_input = input("Downloader> ").strip()
            if not user_input:
                print()
                continue
            command = user_input.lower().split()[0]
            args = user_input.split()[1:]
            try:
                if command == "l":
                    print()
                    self._ds.list(self._ds.download_dir, header=False, more_prompt=True)
                elif command == "h":
                    self._simple_interactive_help()
                elif command == "c":
                    self._simple_interactive_config()
                elif command in ("q", "x"):
                    return
                elif command == "d":
                    self._simple_interactive_download(args)
                elif command == "u":
                    self._simple_interactive_update()
                else:
                    print("Command %r unrecognized" % user_input)
            except HTTPError as e:
                print("Error reading from server: %s" % e)
            except URLError as e:
                print("Error connecting to server: %s" % e.reason)
            # try checking if user_input is a package name, &
            # downloading it?
            print()