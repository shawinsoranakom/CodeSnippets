async def mock_index_repo():
    chat_id = "1"
    chat_path = Path(CHATS_ROOT) / chat_id
    chat_path.mkdir(parents=True, exist_ok=True)
    src_path = TEST_DATA_PATH / "requirements"
    command = f"cp -rf {str(src_path)} {str(chat_path)}"
    os.system(command)
    filenames = list_files(chat_path)
    chat_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    chat_repo = IndexRepo(
        persist_path=str(Path(CHATS_INDEX_ROOT) / chat_id), root_path=str(chat_path), min_token_count=0
    )
    await chat_repo.add(chat_files)
    assert chat_files

    Path(UPLOAD_ROOT).mkdir(parents=True, exist_ok=True)
    command = f"cp -rf {str(src_path)} {str(UPLOAD_ROOT)}"
    os.system(command)
    filenames = list_files(UPLOAD_ROOT)
    uploads_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    assert uploads_files

    filenames = list_files(src_path)
    other_files = [i for i in filenames if Path(i).suffix in {".md", ".txt", ".json", ".pdf"}]
    assert other_files

    return chat_path, UPLOAD_ROOT, src_path