def _edit_file_impl(
        self,
        file_name: Path,
        start: Optional[int] = None,
        end: Optional[int] = None,
        content: str = "",
        is_insert: bool = False,
        is_append: bool = False,
    ) -> str:
        """Internal method to handle common logic for edit_/append_file methods.

        Args:
            file_name: Path: The name of the file to edit or append to.
            start: int | None = None: The start line number for editing. Ignored if is_append is True.
            end: int | None = None: The end line number for editing. Ignored if is_append is True.
            content: str: The content to replace the lines with or to append.
            is_insert: bool = False: Whether to insert content at the given line number instead of editing.
            is_append: bool = False: Whether to append content to the file instead of editing.
        """

        ERROR_MSG = f"[Error editing file {file_name}. Please confirm the file is correct.]"
        ERROR_MSG_SUFFIX = (
            "Your changes have NOT been applied. Please fix your edit command and try again.\n"
            "You either need to 1) Open the correct file and try again or 2) Specify the correct line number arguments.\n"
            "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
        )

        if not self._is_valid_filename(file_name.name):
            raise FileNotFoundError("Invalid file name.")

        if not self._is_valid_path(file_name):
            raise FileNotFoundError("Invalid path or file name.")

        if not self._create_paths(file_name):
            raise PermissionError("Could not access or create directories.")

        if not file_name.is_file():
            raise FileNotFoundError(f"File {file_name} not found.")

        if is_insert and is_append:
            raise ValueError("Cannot insert and append at the same time.")

        # Use a temporary file to write changes
        content = str(content or "")
        temp_file_path = ""
        src_abs_path = file_name.resolve()
        first_error_line = None
        # The file to store previous content and will be removed automatically.
        temp_backup_file = tempfile.NamedTemporaryFile("w", delete=True)

        try:
            # lint the original file
            # enable_auto_lint = os.getenv("ENABLE_AUTO_LINT", "false").lower() == "true"
            if self.enable_auto_lint:
                original_lint_error, _ = self._lint_file(file_name)

            # Create a temporary file
            with tempfile.NamedTemporaryFile("w", delete=False) as temp_file:
                temp_file_path = temp_file.name

                # Read the original file and check if empty and for a trailing newline
                with file_name.open() as original_file:
                    lines = original_file.readlines()

                if is_append:
                    content, n_added_lines = self._append_impl(lines, content)
                elif is_insert:
                    try:
                        content, n_added_lines = self._insert_impl(lines, start, content)
                    except LineNumberError as e:
                        return (f"{ERROR_MSG}\n" f"{e}\n" f"{ERROR_MSG_SUFFIX}") + "\n"
                else:
                    try:
                        content, n_added_lines = self._edit_impl(lines, start, end, content)
                    except LineNumberError as e:
                        return (f"{ERROR_MSG}\n" f"{e}\n" f"{ERROR_MSG_SUFFIX}") + "\n"

                if not content.endswith("\n"):
                    content += "\n"

                # Write the new content to the temporary file
                temp_file.write(content)

            # Replace the original file with the temporary file atomically
            shutil.move(temp_file_path, src_abs_path)

            # Handle linting
            # NOTE: we need to get env var inside this function
            # because the env var will be set AFTER the agentskills is imported
            if self.enable_auto_lint:
                # BACKUP the original file
                temp_backup_file.writelines(lines)
                temp_backup_file.flush()
                lint_error, first_error_line = self._lint_file(file_name)

                # Select the errors caused by the modification
                def extract_last_part(line):
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[-1].strip()
                    return line.strip()

                def subtract_strings(str1, str2) -> str:
                    lines1 = str1.splitlines()
                    lines2 = str2.splitlines()

                    last_parts1 = [extract_last_part(line) for line in lines1]

                    remaining_lines = [line for line in lines2 if extract_last_part(line) not in last_parts1]

                    result = "\n".join(remaining_lines)
                    return result

                if original_lint_error and lint_error:
                    lint_error = subtract_strings(original_lint_error, lint_error)
                    if lint_error == "":
                        lint_error = None
                        first_error_line = None

                if lint_error is not None:
                    # if first_error_line is not None:
                    #     show_line = int(first_error_line)

                    # show the first insert line.
                    if is_append:
                        # original end-of-file
                        show_line = len(lines)
                    # insert OR edit WILL provide meaningful line numbers
                    elif start is not None and end is not None:
                        show_line = int((start + end) / 2)
                    else:
                        raise ValueError("Invalid state. This should never happen.")

                    guidance_message = self._get_indentation_info(content, start or len(lines))
                    guidance_message += (
                        "You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.\n"
                        "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
                    )
                    lint_error_info = ERROR_GUIDANCE.format(
                        linter_error_msg=LINTER_ERROR_MSG + lint_error,
                        window_after_applied=self._print_window(file_name, show_line, n_added_lines + 20),
                        window_before_applied=self._print_window(
                            Path(temp_backup_file.name), show_line, n_added_lines + 20
                        ),
                        guidance_message=guidance_message,
                    ).strip()

                    # recover the original file
                    shutil.move(temp_backup_file.name, src_abs_path)
                    return lint_error_info

        except FileNotFoundError as e:
            return f"File not found: {e}\n"
        except IOError as e:
            return f"An error occurred while handling the file: {e}\n"
        except ValueError as e:
            return f"Invalid input: {e}\n"
        except Exception as e:
            guidance_message = self._get_indentation_info(content, start or len(lines))
            guidance_message += (
                "You either need to 1) Specify the correct start/end line arguments or 2) Enlarge the range of original code.\n"
                "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
            )
            error_info = ERROR_GUIDANCE.format(
                linter_error_msg=LINTER_ERROR_MSG + str(e),
                window_after_applied=self._print_window(file_name, start or len(lines), 100),
                window_before_applied=self._print_window(Path(temp_backup_file.name), start or len(lines), 100),
                guidance_message=guidance_message,
            ).strip()
            # Clean up the temporary file if an error occurs
            shutil.move(temp_backup_file.name, src_abs_path)
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()

            # logger.warning(f"An unexpected error occurred: {e}")
            raise Exception(f"{error_info}") from e
        # Update the file information and print the updated content
        with file_name.open("r", encoding="utf-8") as file:
            n_total_lines = max(1, len(file.readlines()))
        if first_error_line is not None and int(first_error_line) > 0:
            self.current_line = first_error_line
        else:
            if is_append:
                self.current_line = max(1, len(lines))  # end of original file
            else:
                self.current_line = start or n_total_lines or 1
        success_edit_info = SUCCESS_EDIT_INFO.format(
            file_name=file_name.resolve(),
            n_total_lines=n_total_lines,
            window_after_applied=self._print_window(file_name, self.current_line, self.window),
            line_number=self.current_line,
        ).strip()
        return success_edit_info