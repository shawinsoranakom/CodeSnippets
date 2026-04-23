def _output_groups(self) -> None:
        """Move the files to folders.

        Obtains the bins and original filenames from :attr:`_sorter` and outputs into appropriate
        bins in the output location
        """
        is_rename = self._args.sort_method != "none"

        logger.info("Creating %s group folders in '%s'.",
                    len(self._sorter.binned), self._args.output_dir)
        bin_names = [f"_{b}" for b in self._sorter.bin_names]
        if is_rename:
            bin_names = [f"{name}_by_{self._args.sort_method}" for name in bin_names]
        for name in bin_names:
            folder = os.path.join(self._args.output_dir, name)
            if os.path.exists(folder):
                rmtree(folder)
            os.makedirs(folder)

        description = f"{'Copying' if self._args.keep_original else 'Moving'} into groups"
        description += " and renaming" if is_rename else ""

        pbar = tqdm(range(len(self._sorter.sorted_filelist)),
                    desc=description,
                    file=sys.stdout,
                    leave=False)
        idx = 0
        for bin_id, bin_ in enumerate(self._sorter.binned):
            pbar.set_description(f"{description}: Bin {bin_id + 1} of {len(self._sorter.binned)}")
            output_path = os.path.join(self._args.output_dir, bin_names[bin_id])
            if not bin_:
                logger.debug("Removing empty bin: %s", output_path)
                os.rmdir(output_path)
            for source in bin_:
                basename = os.path.basename(source)
                dst_name = f"{idx:06d}_{basename}" if is_rename else basename
                dest = os.path.join(output_path, dst_name)
                self._sort_file(source, dest)
                idx += 1
                pbar.update(1)