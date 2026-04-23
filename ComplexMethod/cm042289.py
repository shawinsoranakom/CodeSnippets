def test_dialogs_do_not_leak():
  gui_app.init_window("ref-test")

  leaked_widgets = set()

  for ctor in (
    # mici
    MiciDriverCameraDialog, MiciPairingDialog,
    lambda: MiciTrainingGuide(lambda: None),
    lambda: MiciOnboardingWindow(lambda: None),
    lambda: BigDialog("test", "test"),
    lambda: BigConfirmationDialog("test", gui_app.texture("icons_mici/settings/network/new/trash.png", 54, 64), lambda: None),
    lambda: BigInputDialog("test"),
    lambda: MiciFccModal(text="test"),
    # tici
    TiciDriverCameraDialog, TiciOnboardingWindow, TiciPairingDialog, Keyboard,
    lambda: ConfirmDialog("test", "ok"),
    lambda: MultiOptionDialog("test", ["a", "b"]),
    lambda: HtmlModal(text="test"),
  ):
    widget = ctor()
    all_refs = [weakref.ref(w) for w in get_child_widgets(widget) + [widget]]

    del widget

    for ref in all_refs:
      if ref() is not None:
        obj = ref()
        name = f"{type(obj).__module__}.{type(obj).__qualname__}"
        leaked_widgets.add(name)

        print(f"\n===  Widget {name} alive after del")
        print("  Referrers:")
        for r in gc.get_referrers(obj):
          if r is obj:
            continue

          if hasattr(r, '__self__') and r.__self__ is not obj:
            print(f"    bound method: {type(r.__self__).__qualname__}.{r.__name__}")
          elif hasattr(r, '__func__'):
            print(f"    method: {r.__name__}")
          else:
            print(f"    {type(r).__module__}.{type(r).__qualname__}")
        del obj

  gui_app.close()

  unexpected = leaked_widgets - KNOWN_LEAKS
  assert not unexpected, f"New leaked widgets: {unexpected}"

  fixed = KNOWN_LEAKS - leaked_widgets
  assert not fixed, f"These leaks are fixed, remove from KNOWN_LEAKS: {fixed}"