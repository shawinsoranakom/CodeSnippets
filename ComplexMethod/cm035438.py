async def write(self, action: FileWriteAction) -> Observation:
        assert self.bash_session is not None
        working_dir = self.bash_session.cwd
        filepath = self._resolve_path(action.path, working_dir)

        insert = action.content.split('\n')
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        file_exists = os.path.exists(filepath)
        if file_exists:
            file_stat = os.stat(filepath)
        else:
            file_stat = None

        mode = 'w' if not file_exists else 'r+'
        try:
            with open(filepath, mode, encoding='utf-8') as file:
                if mode != 'w':
                    all_lines = file.readlines()
                    new_file = insert_lines(insert, all_lines, action.start, action.end)
                else:
                    new_file = [i + '\n' for i in insert]

                file.seek(0)
                file.writelines(new_file)
                file.truncate()

        except FileNotFoundError:
            return ErrorObservation(f'File not found: {filepath}')
        except IsADirectoryError:
            return ErrorObservation(
                f'Path is a directory: {filepath}. You can only write to files'
            )
        except UnicodeDecodeError:
            return ErrorObservation(f'File could not be decoded as utf-8: {filepath}')

        # Attempt to handle file permissions
        try:
            if file_exists:
                assert file_stat is not None
                # restore the original file permissions if the file already exists
                os.chmod(filepath, file_stat.st_mode)
                os.chown(filepath, file_stat.st_uid, file_stat.st_gid)
            else:
                # set the new file permissions if the file is new
                os.chmod(filepath, 0o664)
                os.chown(filepath, self.user_id, self.user_id)
        except PermissionError as e:
            return ErrorObservation(
                f'File {filepath} written, but failed to change ownership and permissions: {e}'
            )
        return FileWriteObservation(content='', path=filepath)