def _call_api_get_tiles(self, video_id, *tile_ids):
        requested_tile_ids = [video_id, *tile_ids]
        requested_tiles = [{'Id': tile_id} for tile_id in requested_tile_ids]
        tiles_response = self._call_api(
            video_id, method='Tile/GetTiles', api_version=2,
            data={'RequestedTiles': requested_tiles})
        tiles = try_get(tiles_response, lambda x: x['Tiles'], list) or []
        if tile_ids:
            if sorted([tile['Id'] for tile in tiles]) != sorted(requested_tile_ids):
                raise ExtractorError('Requested tiles not found', video_id=video_id)
            return tiles
        try:
            return next(tile for tile in tiles if tile['Id'] == video_id)
        except StopIteration:
            raise ExtractorError('No matching tile found', video_id=video_id)