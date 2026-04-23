async def load_bundles_from_urls() -> tuple[list[TemporaryDirectory], list[str]]:
    component_paths: set[str] = set()
    temp_dirs = []
    settings_service = get_settings_service()
    bundle_urls = settings_service.settings.bundle_urls
    if not bundle_urls:
        return [], []

    async with session_scope() as session:
        # Find superuser by role instead of username to avoid issues with credential reset
        from langflow.services.database.models.user.model import User

        stmt = select(User).where(User.is_superuser == True)  # noqa: E712
        result = await session.exec(stmt)
        user = result.first()
        if user is None:
            msg = "No superuser found in the database"
            raise NoResultFound(msg)
        user_id = user.id

        for url in bundle_urls:
            url_ = await detect_github_url(url)

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url_)
                response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
                dir_names = [f.filename for f in zfile.infolist() if f.is_dir() and "/" not in f.filename[:-1]]
                temp_dir = None
                for filename in zfile.namelist():
                    path = Path(filename)
                    for dir_name in dir_names:
                        if path.is_relative_to(f"{dir_name}flows/") and path.suffix == ".json":
                            file_content = zfile.read(filename)
                            await upsert_flow_from_file(file_content, path.stem, session, user_id)
                        elif path.is_relative_to(f"{dir_name}components/"):
                            if temp_dir is None:
                                temp_dir = await asyncio.to_thread(TemporaryDirectory)
                                temp_dirs.append(temp_dir)
                            component_paths.add(str(Path(temp_dir.name) / f"{dir_name}components"))
                            await asyncio.to_thread(zfile.extract, filename, temp_dir.name)

    return temp_dirs, list(component_paths)