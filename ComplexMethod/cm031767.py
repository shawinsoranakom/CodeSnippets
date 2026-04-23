def get_file_platform(file: Path) -> str | None:
    if not file.parts:
        return None
    first_part = file.parts[0]
    if first_part in MACOS_DIRS:
        return "macos"
    if first_part in IOS_DIRS:
        return "ios"
    if first_part in ANDROID_DIRS:
        return "android"
    if len(file.parts) >= 2 and Path(*file.parts[:2]) in EMSCRIPTEN_DIRS:
        return "emscripten"
    if len(file.parts) >= 2 and Path(*file.parts[:2]) in WASI_DIRS:
        return "wasi"
    return None