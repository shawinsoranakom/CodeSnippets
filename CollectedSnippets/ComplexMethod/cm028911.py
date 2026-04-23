def set_frame_processors_modules_from_ui(frame_processors: List[str]) -> None:
    global FRAME_PROCESSORS_MODULES
    current_processor_names = [proc.__name__.split('.')[-1] for proc in FRAME_PROCESSORS_MODULES]

    for frame_processor, state in modules.globals.fp_ui.items():
        if state == True and frame_processor not in current_processor_names:
            try:
                frame_processor_module = load_frame_processor_module(frame_processor)
                FRAME_PROCESSORS_MODULES.append(frame_processor_module)
                if frame_processor not in modules.globals.frame_processors:
                     modules.globals.frame_processors.append(frame_processor)
            except SystemExit:
                 print(f"Warning: Failed to load frame processor {frame_processor} requested by UI state.")
            except Exception as e:
                 print(f"Warning: Error loading frame processor {frame_processor} requested by UI state: {e}")

        elif state == False and frame_processor in current_processor_names:
            try:
                module_to_remove = next((mod for mod in FRAME_PROCESSORS_MODULES if mod.__name__.endswith(f'.{frame_processor}')), None)
                if module_to_remove:
                    FRAME_PROCESSORS_MODULES.remove(module_to_remove)
                if frame_processor in modules.globals.frame_processors:
                    modules.globals.frame_processors.remove(frame_processor)
            except Exception as e:
                 print(f"Warning: Error removing frame processor {frame_processor}: {e}")