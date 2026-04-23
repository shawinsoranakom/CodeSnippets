def rerun_data(self) -> RerunData:
        if self.type is not ScriptRequestType.RERUN:
            raise RuntimeError("RerunData is only set for RERUN requests.")
        return cast(RerunData, self._rerun_data)