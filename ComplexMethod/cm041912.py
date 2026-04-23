def _init_maze(cls, values):
        maze_asset_path = values["maze_asset_path"]
        assert maze_asset_path
        maze_asset_path = Path(maze_asset_path)

        maze_matrix_path = maze_asset_path.joinpath("matrix")
        meta_info = read_json_file(maze_matrix_path.joinpath("maze_meta_info.json"))

        maze_width = int(meta_info["maze_width"])
        maze_height = int(meta_info["maze_height"])
        values["maze_width"] = maze_width
        values["maze_height"] = maze_height
        values["sq_tile_size"] = int(meta_info["sq_tile_size"])
        values["special_constraint"] = meta_info["special_constraint"]

        # READING IN SPECIAL BLOCKS
        # Special blocks are those that are colored in the Tiled map.
        # Here is an example row for the arena block file:
        # e.g, "25331, Double Studio, Studio, Bedroom 2, Painting"

        blocks_folder = maze_matrix_path.joinpath("special_blocks")

        _wb = blocks_folder.joinpath("world_blocks.csv")
        wb_rows = read_csv_to_list(_wb, header=False)
        wb = wb_rows[0][-1]

        _sb = blocks_folder.joinpath("sector_blocks.csv")
        sb_rows = read_csv_to_list(_sb, header=False)
        sb_dict = dict()
        for i in sb_rows:
            sb_dict[i[0]] = i[-1]

        _ab = blocks_folder.joinpath("arena_blocks.csv")
        ab_rows = read_csv_to_list(_ab, header=False)
        ab_dict = dict()
        for i in ab_rows:
            ab_dict[i[0]] = i[-1]

        _gob = blocks_folder.joinpath("game_object_blocks.csv")
        gob_rows = read_csv_to_list(_gob, header=False)
        gob_dict = dict()
        for i in gob_rows:
            gob_dict[i[0]] = i[-1]

        _slb = blocks_folder.joinpath("spawning_location_blocks.csv")
        slb_rows = read_csv_to_list(_slb, header=False)
        slb_dict = dict()
        for i in slb_rows:
            slb_dict[i[0]] = i[-1]

        # [SECTION 3] Reading in the matrices
        # This is your typical two dimensional matrices. It's made up of 0s and
        # the number that represents the color block from the blocks folder.
        maze_folder = maze_matrix_path.joinpath("maze")

        _cm = maze_folder.joinpath("collision_maze.csv")
        collision_maze_raw = read_csv_to_list(_cm, header=False)[0]
        _sm = maze_folder.joinpath("sector_maze.csv")
        sector_maze_raw = read_csv_to_list(_sm, header=False)[0]
        _am = maze_folder.joinpath("arena_maze.csv")
        arena_maze_raw = read_csv_to_list(_am, header=False)[0]
        _gom = maze_folder.joinpath("game_object_maze.csv")
        game_object_maze_raw = read_csv_to_list(_gom, header=False)[0]
        _slm = maze_folder.joinpath("spawning_location_maze.csv")
        spawning_location_maze_raw = read_csv_to_list(_slm, header=False)[0]

        # Loading the maze. The mazes are taken directly from the json exports of
        # Tiled maps. They should be in csv format.
        # Importantly, they are "not" in a 2-d matrix format -- they are single
        # row matrices with the length of width x height of the maze. So we need
        # to convert here.
        # example format: [['0', '0', ... '25309', '0',...], ['0',...]...]
        # 25309 is the collision bar number right now.
        collision_maze = []
        sector_maze = []
        arena_maze = []
        game_object_maze = []
        spawning_location_maze = []
        for i in range(0, len(collision_maze_raw), maze_width):
            tw = maze_width
            collision_maze += [collision_maze_raw[i : i + tw]]
            sector_maze += [sector_maze_raw[i : i + tw]]
            arena_maze += [arena_maze_raw[i : i + tw]]
            game_object_maze += [game_object_maze_raw[i : i + tw]]
            spawning_location_maze += [spawning_location_maze_raw[i : i + tw]]
        values["collision_maze"] = collision_maze

        tiles = []
        for i in range(maze_height):
            row = []
            for j in range(maze_width):
                tile_details = dict()
                tile_details["world"] = wb

                tile_details["sector"] = ""
                if sector_maze[i][j] in sb_dict:
                    tile_details["sector"] = sb_dict[sector_maze[i][j]]

                tile_details["arena"] = ""
                if arena_maze[i][j] in ab_dict:
                    tile_details["arena"] = ab_dict[arena_maze[i][j]]

                tile_details["game_object"] = ""
                if game_object_maze[i][j] in gob_dict:
                    tile_details["game_object"] = gob_dict[game_object_maze[i][j]]

                tile_details["spawning_location"] = ""
                if spawning_location_maze[i][j] in slb_dict:
                    tile_details["spawning_location"] = slb_dict[spawning_location_maze[i][j]]

                tile_details["collision"] = False
                if collision_maze[i][j] != "0":
                    tile_details["collision"] = True

                tile_details["events"] = set()

                row += [tile_details]
            tiles += [row]
        values["tiles"] = tiles

        # Each game object occupies an event in the tile. We are setting up the
        # default event value here.
        for i in range(maze_height):
            for j in range(maze_width):
                if tiles[i][j]["game_object"]:
                    object_name = ":".join(
                        [tiles[i][j]["world"], tiles[i][j]["sector"], tiles[i][j]["arena"], tiles[i][j]["game_object"]]
                    )
                    go_event = (object_name, None, None, None)
                    tiles[i][j]["events"].add(go_event)

        # Reverse tile access.
        # <address_tiles> -- given a string address, we return a set of all
        # tile coordinates belonging to that address (this is opposite of
        # tiles that give you the string address given a coordinate). This is
        # an optimization component for finding paths for the personas' movement.
        # address_tiles['<spawn_loc>bedroom-2-a'] == {(58, 9)}
        # address_tiles['double studio:recreation:pool table']
        #   == {(29, 14), (31, 11), (30, 14), (32, 11), ...},
        address_tiles = dict()
        for i in range(maze_height):
            for j in range(maze_width):
                addresses = []
                if tiles[i][j]["sector"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}'
                    addresses += [add]
                if tiles[i][j]["arena"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}:'
                    add += f'{tiles[i][j]["arena"]}'
                    addresses += [add]
                if tiles[i][j]["game_object"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}:'
                    add += f'{tiles[i][j]["arena"]}:'
                    add += f'{tiles[i][j]["game_object"]}'
                    addresses += [add]
                if tiles[i][j]["spawning_location"]:
                    add = f'<spawn_loc>{tiles[i][j]["spawning_location"]}'
                    addresses += [add]

                for add in addresses:
                    if add in address_tiles:
                        address_tiles[add].add((j, i))
                    else:
                        address_tiles[add] = set([(j, i)])
        values["address_tiles"] = address_tiles

        values["action_space"] = get_action_space((maze_width, maze_height))
        values["observation_space"] = get_observation_space()
        return values