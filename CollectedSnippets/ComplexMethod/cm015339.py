def forward(self, inputs):
                assert self.modulelist[0] is self.submod, (  # noqa: S101
                    "__getitem__ failing for ModuleList"
                )
                assert len(self.modulelist) == 1, "__len__ failing for ModuleList"  # noqa: S101
                for module in self.modulelist:
                    assert module is self.submod, "__iter__ failing for ModuleList"  # noqa: S101

                assert self.sequential[0] is self.submod, (  # noqa: S101
                    "__getitem__ failing for Sequential"
                )
                assert len(self.sequential) == 1, "__len__ failing for Sequential"  # noqa: S101
                for module in self.sequential:
                    assert module is self.submod, "__iter__ failing for Sequential"  # noqa: S101

                assert self.moduledict["submod"] is self.submod, (  # noqa: S101
                    "__getitem__ failing for ModuleDict"
                )
                assert len(self.moduledict) == 1, "__len__ failing for ModuleDict"  # noqa: S101

                # note: unable to index moduledict with a string variable currently
                i = 0
                for _ in self.moduledict:
                    i += 1
                assert i == len(self.moduledict), "iteration failing for ModuleDict"  # noqa: S101

                assert "submod" in self.moduledict, "__contains__ fails for ModuleDict"  # noqa: S101

                for key in self.moduledict:
                    assert key == "submod", "keys() fails for ModuleDict"  # noqa: S101

                for item in self.moduledict.items():
                    assert item[0] == "submod", "items() fails for ModuleDict"  # noqa: S101
                    assert item[1] is self.submod, "items() fails for ModuleDict"  # noqa: S101

                for value in self.moduledict.values():
                    assert value is self.submod, "values() fails for ModuleDict"  # noqa: S101

                return inputs