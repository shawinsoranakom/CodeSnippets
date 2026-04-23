def add_tile_info(self, tile_info: dict) -> None:
        if tile_info["world"]:
            if tile_info["world"] not in self.tree:
                self.tree[tile_info["world"]] = {}
        if tile_info["sector"]:
            if tile_info["sector"] not in self.tree[tile_info["world"]]:
                self.tree[tile_info["world"]][tile_info["sector"]] = {}
        if tile_info["arena"]:
            if tile_info["arena"] not in self.tree[tile_info["world"]][tile_info["sector"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] = []
        if tile_info["game_object"]:
            if tile_info["game_object"] not in self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] += [tile_info["game_object"]]