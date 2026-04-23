async def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        if self.browser is None:
            return ErrorObservation(
                'Browser functionality is not supported or disabled.'
            )
        await self._ensure_browser_ready()
        browser_observation = await browse(action, self.browser, self.initial_cwd)
        if not browser_observation.error:
            return browser_observation
        else:
            curr_files = os.listdir(self.downloads_directory)
            new_download = False
            for file in curr_files:
                if file not in self.downloaded_files:
                    new_download = True
                    self.downloaded_files.append(file)
                    break  # FIXME: assuming only one file will be downloaded for simplicity

            if not new_download:
                return browser_observation
            else:
                # A new file is downloaded in self.downloads_directory, shift file to /workspace
                src_path = os.path.join(
                    self.downloads_directory, self.downloaded_files[-1]
                )
                # Guess extension of file using puremagic and add it to tgt_path file name
                file_ext = ''
                try:
                    guesses = puremagic.magic_file(src_path)
                    if len(guesses) > 0:
                        ext = guesses[0].extension.strip()
                        if len(ext) > 0:
                            file_ext = ext
                except Exception as _:
                    pass

                tgt_path = os.path.join(
                    '/workspace', f'file_{len(self.downloaded_files)}{file_ext}'
                )
                shutil.copy(src_path, tgt_path)
                file_download_obs = FileDownloadObservation(
                    content=f'Execution of the previous action {action.browser_actions} resulted in a file download. The downloaded file is saved at location: {tgt_path}',
                    file_path=tgt_path,
                )
                return file_download_obs