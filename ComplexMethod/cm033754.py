def __post_init__(self):
        assert pathlib.PurePosixPath(self.path).is_relative_to(CGroupPath.ROOT)

        if self.type is None:
            assert self.state is None
        elif self.type == MountType.TMPFS:
            assert self.writable is True
            assert self.state is None
        else:
            assert self.type in (MountType.CGROUP_V1, MountType.CGROUP_V2)
            assert self.state is not None