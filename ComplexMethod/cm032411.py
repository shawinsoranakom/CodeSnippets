def output_collation(self):
        pid = self.get_parent()._id
        for cid in self._canvas.components.keys():
            obj = self._canvas.get_component_obj(cid)
            p = obj.get_parent()
            if not p:
                continue
            if p._id != pid:
                continue

            if p.component_name.lower() in ["categorize", "message", "switch", "userfillup", "iterationitem"]:
                continue

            for k, o in p._param.outputs.items():
                if "ref" not in o:
                    continue
                _cid, var = o["ref"].split("@")
                if _cid != cid:
                    continue
                res = p.output(k)
                if not res:
                    res = []
                res.append(obj.output(var))
                p.set_output(k, res)