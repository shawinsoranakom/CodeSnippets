async def _resolve_reference_assets(
    cls: type[IO.ComfyNode],
    asset_ids: list[str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Look up each asset, validate Active status, group by asset_type.

    Returns (image_assets, video_assets, audio_assets), each mapping asset_id -> "asset://<asset_id>".
    """
    image_assets: dict[str, str] = {}
    video_assets: dict[str, str] = {}
    audio_assets: dict[str, str] = {}
    for i, raw_id in enumerate(asset_ids, 1):
        asset_id = (raw_id or "").strip()
        if not asset_id:
            continue
        result = await sync_op(
            cls,
            ApiEndpoint(path=f"/proxy/seedance/assets/{asset_id}"),
            response_model=GetAssetResponse,
        )
        if result.status != "Active":
            extra = f" {result.error.code}: {result.error.message}" if result.error else ""
            raise ValueError(f"Reference asset {i} (Id={asset_id}) is not Active (Status={result.status}).{extra}")
        asset_uri = f"asset://{asset_id}"
        if result.asset_type == "Image":
            image_assets[asset_id] = asset_uri
        elif result.asset_type == "Video":
            video_assets[asset_id] = asset_uri
        elif result.asset_type == "Audio":
            audio_assets[asset_id] = asset_uri
    return image_assets, video_assets, audio_assets