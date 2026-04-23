def test_e2e(self):
        model = TopModel(self.rank).to(self.device_type)

        mesh_fsdp_tp = init_device_mesh(
            self.device_type, (2, 4), mesh_dim_names=("dp", "tp")
        )
        # TODO: we are using an internal API atm. Change to a public API once it is ready.
        mesh_fsdp_ep = mesh_fsdp_tp["dp"]
        mesh_fsdp_ep._root_mesh = None

        mesh_fsdp = init_device_mesh(self.device_type, (8,))
        for i, l in enumerate(model.second.ep_layers):
            model.second.ep_layers[i] = FSDP(
                l, use_orig_params=True, device_mesh=mesh_fsdp_ep
            )
        model.second = FSDP(model.second, use_orig_params=True, device_mesh=mesh_fsdp)
        model = FSDP(model, use_orig_params=True, device_mesh=mesh_fsdp)
        optim = torch.optim.Adam(model.parameters(), lr=0.1)
        msd, osd = get_state_dict(model, optim)

        # FSDP only params
        for key in (
            "net.0.weight",
            "net.0.bias",
            "second.net.0.weight",
            "second.net.0.bias",
        ):
            msd_v = msd[key]
            osd_v = osd["state"][key]["exp_avg"]
            for v in (msd_v, osd_v):
                self.assertTrue(isinstance(v, DTensor))
                self.assertEqual(tuple(v.device_mesh.mesh), tuple(range(8)))

        # FSDP/EP params
        layer = self.rank % 4
        ranks = (layer, layer + 4)
        for i in range(4):
            for key in (
                f"second.ep_layers.{i}.net1.0.weight",
                f"second.ep_layers.{i}.net1.0.bias",
                f"second.ep_layers.{i}.net2.0.weight",
                f"second.ep_layers.{i}.net2.0.bias",
            ):
                if layer != i:
                    self.assertTrue(key not in msd)
                else:
                    msd_v = msd[key]
                    osd_v = osd["state"][key]["exp_avg"]
                    for v in (msd_v, osd_v):
                        self.assertTrue(isinstance(v, DTensor))
                        self.assertEqual(tuple(v.device_mesh.mesh), ranks)

        self.assertEqual(set(osd["state"].keys()), set(msd.keys()))