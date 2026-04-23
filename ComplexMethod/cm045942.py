def forward(self, x):
        y = dict()
        if self.use_backbone:
            x = self.backbone(x)
        if isinstance(x, dict):
            y.update(x)
        else:
            y["backbone_out"] = x
        final_name = "backbone_out"
        if self.use_neck:
            x = self.neck(x)
            if isinstance(x, dict):
                y.update(x)
            else:
                y["neck_out"] = x
            final_name = "neck_out"
        if self.use_head:
            x = self.head(x)
        # for multi head, save ctc neck out for udml
        if isinstance(x, dict) and "ctc_nect" in x.keys():
            y["neck_out"] = x["ctc_neck"]
            y["head_out"] = x
        elif isinstance(x, dict):
            y.update(x)
        else:
            y["head_out"] = x
        if self.return_all_feats:
            if self.training:
                return y
            elif isinstance(x, dict):
                return x
            else:
                return {final_name: x}
        else:
            return x