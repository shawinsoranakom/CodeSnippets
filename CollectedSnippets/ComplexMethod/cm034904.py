def forward(self, preds, labels):
        assert isinstance(preds, dict)
        preds = preds["levels"]

        p3_maps, p4_maps, p5_maps = labels[1:]
        assert (
            p3_maps[0].shape[0] == 4 * self.fourier_degree + 5
        ), "fourier degree not equal in FCEhead and FCEtarget"

        # to tensor
        gts = [p3_maps, p4_maps, p5_maps]
        for idx, maps in enumerate(gts):
            gts[idx] = paddle.to_tensor(np.stack(maps))

        losses = multi_apply(self.forward_single, preds, gts)

        loss_tr = paddle.to_tensor(0.0).astype("float32")
        loss_tcl = paddle.to_tensor(0.0).astype("float32")
        loss_reg_x = paddle.to_tensor(0.0).astype("float32")
        loss_reg_y = paddle.to_tensor(0.0).astype("float32")
        loss_all = paddle.to_tensor(0.0).astype("float32")

        for idx, loss in enumerate(losses):
            loss_all += sum(loss)
            if idx == 0:
                loss_tr += sum(loss)
            elif idx == 1:
                loss_tcl += sum(loss)
            elif idx == 2:
                loss_reg_x += sum(loss)
            else:
                loss_reg_y += sum(loss)

        results = dict(
            loss=loss_all,
            loss_text=loss_tr,
            loss_center=loss_tcl,
            loss_reg_x=loss_reg_x,
            loss_reg_y=loss_reg_y,
        )
        return results