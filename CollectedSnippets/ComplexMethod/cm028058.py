def _get_obs(self):
    # No cfrc observation
    if self._expose_all_qpos:
      obs = np.concatenate([
          self.physics.data.qpos.flat[:15],  # Ensures only ant obs.
          self.physics.data.qvel.flat[:14],
      ])
    else:
      obs = np.concatenate([
          self.physics.data.qpos.flat[2:15],
          self.physics.data.qvel.flat[:14],
      ])

    if self._expose_body_coms is not None:
      for name in self._expose_body_coms:
        com = self.get_body_com(name)
        if name not in self._body_com_indices:
          indices = range(len(obs), len(obs) + len(com))
          self._body_com_indices[name] = indices
        obs = np.concatenate([obs, com])

    if self._expose_body_comvels is not None:
      for name in self._expose_body_comvels:
        comvel = self.get_body_comvel(name)
        if name not in self._body_comvel_indices:
          indices = range(len(obs), len(obs) + len(comvel))
          self._body_comvel_indices[name] = indices
        obs = np.concatenate([obs, comvel])
    return obs