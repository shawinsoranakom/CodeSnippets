async def _create_system_design(self):
        action = RebuildClassView(
            name="ReverseEngineering", i_context=str(self.context.src_workspace), context=self.context
        )
        await action.run()
        rows = await action.graph_db.select(predicate="hasMermaidClassDiagramFile")
        class_view_filename = rows[0].object_
        logger.info(f"class view:{class_view_filename}")

        rows = await action.graph_db.select(predicate=GraphKeyword.HAS_PAGE_INFO)
        tag = "__name__:__main__"
        entries = []
        src_workspace = self.context.src_workspace.relative_to(self.context.repo.workdir)
        for r in rows:
            if tag in r.subject:
                path = split_namespace(r.subject)[0]
            elif tag in r.object_:
                path = split_namespace(r.object_)[0]
            else:
                continue
            if Path(path).is_relative_to(src_workspace):
                entries.append(Path(path))
        main_entry = await self._guess_main_entry(entries)
        full_path = RebuildSequenceView.get_full_filename(self.context.repo.workdir, main_entry)
        action = RebuildSequenceView(context=self.context, i_context=str(full_path))
        try:
            await action.run()
        except Exception as e:
            logger.warning(f"{e}, use the last successful version.")
        files = list_files(self.context.repo.resources.data_api_design.workdir)
        pattern = re.compile(r"[^a-zA-Z0-9]")
        name = re.sub(pattern, "_", str(main_entry))
        filename = Path(name).with_suffix(".sequence_diagram.mmd")
        postfix = str(filename)
        sequence_files = [i for i in files if postfix in str(i)]
        content = await aread(filename=sequence_files[0])
        await self.context.repo.resources.data_api_design.save(
            filename=self.repo.workdir.stem + ".sequence_diagram.mmd", content=content
        )
        await self._save_system_design()