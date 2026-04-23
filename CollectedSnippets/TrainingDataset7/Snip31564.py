def setup_gc_debug(self):
        self.addCleanup(gc.set_debug, 0)
        self.addCleanup(gc.enable)
        gc.disable()
        garbage_collect()
        gc.set_debug(gc.DEBUG_SAVEALL)