def __init__(
      self,
      maze_id=None,
      maze_height=0.5,
      maze_size_scaling=8,
      n_bins=0,
      sensor_range=3.,
      sensor_span=2 * math.pi,
      observe_blocks=False,
      put_spin_near_agent=False,
      top_down_view=False,
      manual_collision=False,
      *args,
      **kwargs):
    self._maze_id = maze_id

    model_cls = self.__class__.MODEL_CLASS
    if model_cls is None:
      raise "MODEL_CLASS unspecified!"
    xml_path = os.path.join(MODEL_DIR, model_cls.FILE)
    tree = ET.parse(xml_path)
    worldbody = tree.find(".//worldbody")

    self.MAZE_HEIGHT = height = maze_height
    self.MAZE_SIZE_SCALING = size_scaling = maze_size_scaling
    self._n_bins = n_bins
    self._sensor_range = sensor_range * size_scaling
    self._sensor_span = sensor_span
    self._observe_blocks = observe_blocks
    self._put_spin_near_agent = put_spin_near_agent
    self._top_down_view = top_down_view
    self._manual_collision = manual_collision

    self.MAZE_STRUCTURE = structure = maze_env_utils.construct_maze(maze_id=self._maze_id)
    self.elevated = any(-1 in row for row in structure)  # Elevate the maze to allow for falling.
    self.blocks = any(
        any(maze_env_utils.can_move(r) for r in row)
        for row in structure)  # Are there any movable blocks?

    torso_x, torso_y = self._find_robot()
    self._init_torso_x = torso_x
    self._init_torso_y = torso_y
    self._init_positions = [
        (x - torso_x, y - torso_y)
        for x, y in self._find_all_robots()]

    self._xy_to_rowcol = lambda x, y: (2 + (y + size_scaling / 2) / size_scaling,
                                       2 + (x + size_scaling / 2) / size_scaling)
    self._view = np.zeros([5, 5, 3])  # walls (immovable), chasms (fall), movable blocks

    height_offset = 0.
    if self.elevated:
      # Increase initial z-pos of ant.
      height_offset = height * size_scaling
      torso = tree.find(".//body[@name='torso']")
      torso.set('pos', '0 0 %.2f' % (0.75 + height_offset))
    if self.blocks:
      # If there are movable blocks, change simulation settings to perform
      # better contact detection.
      default = tree.find(".//default")
      default.find('.//geom').set('solimp', '.995 .995 .01')

    self.movable_blocks = []
    for i in range(len(structure)):
      for j in range(len(structure[0])):
        struct = structure[i][j]
        if struct == 'r' and self._put_spin_near_agent:
          struct = maze_env_utils.Move.SpinXY
        if self.elevated and struct not in [-1]:
          # Create elevated platform.
          ET.SubElement(
              worldbody, "geom",
              name="elevated_%d_%d" % (i, j),
              pos="%f %f %f" % (j * size_scaling - torso_x,
                                i * size_scaling - torso_y,
                                height / 2 * size_scaling),
              size="%f %f %f" % (0.5 * size_scaling,
                                 0.5 * size_scaling,
                                 height / 2 * size_scaling),
              type="box",
              material="",
              contype="1",
              conaffinity="1",
              rgba="0.9 0.9 0.9 1",
          )
        if struct == 1:  # Unmovable block.
          # Offset all coordinates so that robot starts at the origin.
          ET.SubElement(
              worldbody, "geom",
              name="block_%d_%d" % (i, j),
              pos="%f %f %f" % (j * size_scaling - torso_x,
                                i * size_scaling - torso_y,
                                height_offset +
                                height / 2 * size_scaling),
              size="%f %f %f" % (0.5 * size_scaling,
                                 0.5 * size_scaling,
                                 height / 2 * size_scaling),
              type="box",
              material="",
              contype="1",
              conaffinity="1",
              rgba="0.4 0.4 0.4 1",
          )
        elif maze_env_utils.can_move(struct):  # Movable block.
          # The "falling" blocks are shrunk slightly and increased in mass to
          # ensure that it can fall easily through a gap in the platform blocks.
          name = "movable_%d_%d" % (i, j)
          self.movable_blocks.append((name, struct))
          falling = maze_env_utils.can_move_z(struct)
          spinning = maze_env_utils.can_spin(struct)
          x_offset = 0.25 * size_scaling if spinning else 0.0
          y_offset = 0.0
          shrink = 0.1 if spinning else 0.99 if falling else 1.0
          height_shrink = 0.1 if spinning else 1.0
          movable_body = ET.SubElement(
              worldbody, "body",
              name=name,
              pos="%f %f %f" % (j * size_scaling - torso_x + x_offset,
                                i * size_scaling - torso_y + y_offset,
                                height_offset +
                                height / 2 * size_scaling * height_shrink),
          )
          ET.SubElement(
              movable_body, "geom",
              name="block_%d_%d" % (i, j),
              pos="0 0 0",
              size="%f %f %f" % (0.5 * size_scaling * shrink,
                                 0.5 * size_scaling * shrink,
                                 height / 2 * size_scaling * height_shrink),
              type="box",
              material="",
              mass="0.001" if falling else "0.0002",
              contype="1",
              conaffinity="1",
              rgba="0.9 0.1 0.1 1"
          )
          if maze_env_utils.can_move_x(struct):
            ET.SubElement(
                movable_body, "joint",
                armature="0",
                axis="1 0 0",
                damping="0.0",
                limited="true" if falling else "false",
                range="%f %f" % (-size_scaling, size_scaling),
                margin="0.01",
                name="movable_x_%d_%d" % (i, j),
                pos="0 0 0",
                type="slide"
            )
          if maze_env_utils.can_move_y(struct):
            ET.SubElement(
                movable_body, "joint",
                armature="0",
                axis="0 1 0",
                damping="0.0",
                limited="true" if falling else "false",
                range="%f %f" % (-size_scaling, size_scaling),
                margin="0.01",
                name="movable_y_%d_%d" % (i, j),
                pos="0 0 0",
                type="slide"
            )
          if maze_env_utils.can_move_z(struct):
            ET.SubElement(
                movable_body, "joint",
                armature="0",
                axis="0 0 1",
                damping="0.0",
                limited="true",
                range="%f 0" % (-height_offset),
                margin="0.01",
                name="movable_z_%d_%d" % (i, j),
                pos="0 0 0",
                type="slide"
            )
          if maze_env_utils.can_spin(struct):
            ET.SubElement(
                movable_body, "joint",
                armature="0",
                axis="0 0 1",
                damping="0.0",
                limited="false",
                name="spinable_%d_%d" % (i, j),
                pos="0 0 0",
                type="ball"
            )

    torso = tree.find(".//body[@name='torso']")
    geoms = torso.findall(".//geom")
    for geom in geoms:
      if 'name' not in geom.attrib:
        raise Exception("Every geom of the torso must have a name "
                        "defined")

    _, file_path = tempfile.mkstemp(text=True, suffix='.xml')
    tree.write(file_path)

    self.wrapped_env = model_cls(*args, file_path=file_path, **kwargs)