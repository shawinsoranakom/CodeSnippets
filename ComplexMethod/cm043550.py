def call_exe(self, other_args: list[str]):
        """Process exe command."""
        # Merge rest of string path to other_args and remove queue since it is a dir
        other_args += self.queue

        if not other_args:
            session.console.print(
                "[info]Provide a path to the routine you wish to execute. For an example, please use "
                "`exe --example`.\n[/info]"
            )
            return
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="exe",
            description="Execute automated routine script. For an example, please use `exe --example`.",
        )
        parser.add_argument(
            "--file",
            "-f",
            help="The path or .openbb file to run.",
            dest="file",
            required="-h" not in other_args
            and "--help" not in other_args
            and "-e" not in other_args
            and "--example" not in other_args
            and "--url" not in other_args
            and "my.openbb" not in other_args[0],
            type=str,
            nargs="+",
        )
        parser.add_argument(
            "-i",
            "--input",
            help="Select multiple inputs to be replaced in the routine and separated by commas. E.g. GME,AMC,BTC-USD",
            dest="routine_args",
            type=str,
        )
        parser.add_argument(
            "-e",
            "--example",
            help="Run an example script to understand how routines can be used.",
            dest="example",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--url", help="URL to run openbb script from.", dest="url", type=str
        )
        if other_args and "-" not in other_args[0][0]:
            if other_args[0].startswith("my.") or other_args[0].startswith("http"):
                other_args.insert(0, "--url")
            else:
                other_args.insert(0, "--file")
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if ns_parser.example:
                routine_path = ASSETS_DIRECTORY / "routines" / "routine_example.openbb"
                session.console.print(  # TODO: Point to docs when ready
                    "[info]Executing an example, please visit our docs to learn how to create your own script.[/info]\n"
                )
                time.sleep(3)
            elif ns_parser.url:
                if not ns_parser.url.startswith(
                    "https"
                ) and not ns_parser.url.startswith("http:"):
                    url = "https://" + ns_parser.url
                elif ns_parser.url.startswith("http://"):
                    url = ns_parser.url.replace("http://", "https://")
                else:
                    url = ns_parser.url
                username = url.split("/")[-3]
                script_name = url.split("/")[-1]
                file_name = f"{username}_{script_name}.openbb"
                final_url = f"{url}?raw=true"
                response = requests.get(final_url, timeout=10)
                if response.status_code != 200:
                    session.console.print(
                        "[red]Could not find the requested script.[/red]"
                    )
                    return
                routine_text = response.json()["script"]
                file_path = Path(session.user.preferences.export_directory, "routines")
                routine_path = file_path / file_name
                with open(routine_path, "w") as file:
                    file.write(routine_text)
                self.update_runtime_choices()

            elif ns_parser.file:
                file_path = " ".join(ns_parser.file)  # type: ignore
                # if string is not in this format "default/file.openbb" then check for files in ROUTINE_FILES
                full_path = file_path
                hub_routine = file_path.split("/")  # type: ignore
                # Change with: my.openbb.co
                if hub_routine[0] == "default":
                    routine_path = Path(
                        self.ROUTINE_DEFAULT_FILES.get(hub_routine[1], full_path)
                    )
                elif hub_routine[0] == "personal":
                    routine_path = Path(
                        self.ROUTINE_PERSONAL_FILES.get(hub_routine[1], full_path)
                    )
                else:
                    routine_path = Path(self.ROUTINE_FILES.get(file_path, full_path))  # type: ignore
            else:
                return

            try:
                with open(routine_path) as fp:
                    raw_lines = list(fp)

                script_inputs = []
                # Capture ARGV either as list if args separated by commas or as single value
                if routine_args := ns_parser.routine_args:
                    pattern = r"\[(.*?)\]"
                    matches = re.findall(pattern, routine_args)

                    for match in matches:
                        routine_args = routine_args.replace(f"[{match}]", "")
                        script_inputs.append(match)

                    script_inputs.extend(
                        [val for val in routine_args.split(",") if val]
                    )

                err, parsed_script = parse_openbb_script(
                    raw_lines=raw_lines, script_inputs=script_inputs
                )

                # If there err output is not an empty string then it means there was an
                # issue in parsing the routine and therefore we don't want to feed it
                # to the terminal
                if err:
                    session.console.print(err)
                    return

                self.queue = [
                    val
                    for val in parse_and_split_input(
                        an_input=parsed_script, custom_filters=[]
                    )
                    if val
                ]

                if "export" in self.queue[0]:
                    export_path = self.queue[0].split(" ")[1]
                    # If the path selected does not start from the user root, give relative location from root
                    if export_path[0] == "~":
                        export_path = export_path.replace(
                            "~", HOME_DIRECTORY.as_posix()
                        )
                    elif export_path[0] != "/":
                        export_path = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)), export_path
                        )

                    # Check if the directory exists
                    if os.path.isdir(export_path):
                        session.console.print(
                            f"Export data to be saved in the selected folder: '{export_path}'"
                        )
                    else:
                        os.makedirs(export_path)
                        session.console.print(
                            f"[green]Folder '{export_path}' successfully created.[/green]"
                        )
                    self.queue = self.queue[1:]

            except FileNotFoundError:
                session.console.print(
                    f"[red]File '{routine_path}' doesn't exist.[/red]"
                )
                return