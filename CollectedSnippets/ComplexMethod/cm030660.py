def cb2(self, phase, info):
        self.visit.append((2, phase, dict(info)))
        if phase == "stop" and hasattr(self, "cleanup"):
            # Clean Uncollectable from garbage
            uc = [e for e in gc.garbage if isinstance(e, Uncollectable)]
            gc.garbage[:] = [e for e in gc.garbage
                             if not isinstance(e, Uncollectable)]
            for e in uc:
                e.partner = None