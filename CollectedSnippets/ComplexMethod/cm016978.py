async def download_and_extract_obj_zip(url: str) -> ObjZipResult:
    """The Tencent API returns OBJ results as ZIP archives containing the .obj mesh, and texture images.

    When PBR is enabled, the ZIP may contain additional metallic, normal, and roughness maps
    identified by their filename suffixes.
    """
    data = BytesIO()
    await download_url_to_bytesio(url, data)
    data.seek(0)
    if not zipfile.is_zipfile(data):
        data.seek(0)
        return ObjZipResult(obj=Types.File3D(source=data, file_format="obj"))
    data.seek(0)
    obj_bytes = None
    textures: dict[str, Input.Image] = {}
    with zipfile.ZipFile(data) as zf:
        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith(".obj"):
                obj_bytes = zf.read(name)
            elif any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
                stem = lower.rsplit(".", 1)[0]
                tensor = bytesio_to_image_tensor(BytesIO(zf.read(name)), mode="RGB")
                matched_key = "texture"
                for suffix, key in {
                    "_metallic": "metallic",
                    "_normal": "normal",
                    "_roughness": "roughness",
                }.items():
                    if stem.endswith(suffix):
                        matched_key = key
                        break
                textures[matched_key] = tensor
    if obj_bytes is None:
        raise ValueError("ZIP archive does not contain an OBJ file.")
    return ObjZipResult(
        obj=Types.File3D(source=BytesIO(obj_bytes), file_format="obj"),
        texture=textures.get("texture"),
        metallic=textures.get("metallic"),
        normal=textures.get("normal"),
        roughness=textures.get("roughness"),
    )