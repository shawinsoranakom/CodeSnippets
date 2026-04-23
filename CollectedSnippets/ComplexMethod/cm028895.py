def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label, show_fps_switch

    load_switch_states()

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme(resolve_relative_path("ui.json"))

    root = ctk.CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(
        f"{modules.metadata.name} {modules.metadata.version} {modules.metadata.edition}"
    )
    root.configure()
    root.protocol("WM_DELETE_WINDOW", lambda: destroy())

    source_label = ctk.CTkLabel(root, text=None)
    source_label.place(relx=0.1, rely=0.05, relwidth=0.275, relheight=0.225)

    target_label = ctk.CTkLabel(root, text=None)
    target_label.place(relx=0.6, rely=0.05, relwidth=0.275, relheight=0.225)

    select_face_button = ctk.CTkButton(
        root, text=_("Select a face"), cursor="hand2", command=lambda: select_source_path()
    )
    select_face_button.place(relx=0.1, rely=0.30, relwidth=0.24, relheight=0.1)
    ToolTip(select_face_button, _("Choose the source face image to swap onto the target"))

    random_face_button = ctk.CTkButton(
        root, text="🔄", cursor="hand2", width=30, command=lambda: fetch_random_face()
    )
    random_face_button.place(relx=0.35, rely=0.30, relwidth=0.05, relheight=0.1)
    ToolTip(random_face_button, _("Get a random face from thispersondoesnotexist.com"))

    swap_faces_button = ctk.CTkButton(
        root, text="↔", cursor="hand2", command=lambda: swap_faces_paths()
    )
    swap_faces_button.place(relx=0.45, rely=0.30, relwidth=0.1, relheight=0.1)
    ToolTip(swap_faces_button, _("Swap source and target images"))

    select_target_button = ctk.CTkButton(
        root,
        text=_("Select a target"),
        cursor="hand2",
        command=lambda: select_target_path(),
    )
    select_target_button.place(relx=0.6, rely=0.30, relwidth=0.3, relheight=0.1)
    ToolTip(select_target_button, _("Choose the target image or video to apply face swap to"))

    keep_fps_value = ctk.BooleanVar(value=modules.globals.keep_fps)
    keep_fps_checkbox = ctk.CTkSwitch(
        root,
        text=_("Keep fps"),
        variable=keep_fps_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "keep_fps", keep_fps_value.get()),
            save_switch_states(),
        ),
    )
    keep_fps_checkbox.place(relx=0.1, rely=0.42)
    ToolTip(keep_fps_checkbox, _("Output video keeps the original frame rate"))

    keep_frames_value = ctk.BooleanVar(value=modules.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(
        root,
        text=_("Keep frames"),
        variable=keep_frames_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "keep_frames", keep_frames_value.get()),
            save_switch_states(),
        ),
    )
    keep_frames_switch.place(relx=0.1, rely=0.47)
    ToolTip(keep_frames_switch, _("Keep extracted frames on disk after processing"))

    keep_audio_value = ctk.BooleanVar(value=modules.globals.keep_audio)
    keep_audio_switch = ctk.CTkSwitch(
        root,
        text=_("Keep audio"),
        variable=keep_audio_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "keep_audio", keep_audio_value.get()),
            save_switch_states(),
        ),
    )
    keep_audio_switch.place(relx=0.6, rely=0.42)
    ToolTip(keep_audio_switch, _("Copy audio track from the source video to output"))

    many_faces_value = ctk.BooleanVar(value=modules.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(
        root,
        text=_("Many faces"),
        variable=many_faces_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "many_faces", many_faces_value.get()),
            save_switch_states(),
        ),
    )
    many_faces_switch.place(relx=0.6, rely=0.47)
    ToolTip(many_faces_switch, _("Swap every detected face, not just the primary one"))

    color_correction_value = ctk.BooleanVar(value=modules.globals.color_correction)
    color_correction_switch = ctk.CTkSwitch(
        root,
        text=_("Fix Blueish Cam"),
        variable=color_correction_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "color_correction", color_correction_value.get()),
            save_switch_states(),
        ),
    )
    color_correction_switch.place(relx=0.6, rely=0.57)
    ToolTip(color_correction_switch, _("Fix blue/green color cast from some webcams"))

    #    nsfw_value = ctk.BooleanVar(value=modules.globals.nsfw_filter)
    #    nsfw_switch = ctk.CTkSwitch(root, text='NSFW filter', variable=nsfw_value, cursor='hand2', command=lambda: setattr(modules.globals, 'nsfw_filter', nsfw_value.get()))
    #    nsfw_switch.place(relx=0.6, rely=0.7)

    map_faces = ctk.BooleanVar(value=modules.globals.map_faces)
    map_faces_switch = ctk.CTkSwitch(
        root,
        text=_("Map faces"),
        variable=map_faces,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "map_faces", map_faces.get()),
            save_switch_states(),
            close_mapper_window() if not map_faces.get() else None
        ),
    )
    map_faces_switch.place(relx=0.1, rely=0.52)
    ToolTip(map_faces_switch, _("Manually assign which source face maps to which target face"))

    poisson_blend_value = ctk.BooleanVar(value=modules.globals.poisson_blend)
    poisson_blend_switch = ctk.CTkSwitch(
        root,
        text=_("Poisson Blend"),
        variable=poisson_blend_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "poisson_blend", poisson_blend_value.get()),
            save_switch_states(),
        ),
    )
    poisson_blend_switch.place(relx=0.1, rely=0.57)
    ToolTip(poisson_blend_switch, _("Blend face edges smoothly using Poisson blending"))

    show_fps_value = ctk.BooleanVar(value=modules.globals.show_fps)
    show_fps_switch = ctk.CTkSwitch(
        root,
        text=_("Show FPS"),
        variable=show_fps_value,
        cursor="hand2",
        command=lambda: (
            setattr(modules.globals, "show_fps", show_fps_value.get()),
            save_switch_states(),
        ),
    )
    show_fps_switch.place(relx=0.6, rely=0.52)
    ToolTip(show_fps_switch, _("Display frames-per-second counter on the live preview"))

    # mouth_mask and show_mouth_mask_box are auto-controlled by the Mouth Mask slider
    mouth_mask_var = ctk.BooleanVar(value=modules.globals.mouth_mask)
    show_mouth_mask_box_var = ctk.BooleanVar(value=modules.globals.show_mouth_mask_box)

    start_button = ctk.CTkButton(
        root, text=_("Start"), cursor="hand2", command=lambda: analyze_target(start, root)
    )
    start_button.place(relx=0.15, rely=0.78, relwidth=0.2, relheight=0.04)
    ToolTip(start_button, _("Begin processing the target image/video with selected face"))

    stop_button = ctk.CTkButton(
        root, text=_("Destroy"), cursor="hand2", command=lambda: destroy()
    )
    stop_button.place(relx=0.4, rely=0.78, relwidth=0.2, relheight=0.04)
    ToolTip(stop_button, _("Stop processing and close the application"))

    preview_button = ctk.CTkButton(
        root, text=_("Preview"), cursor="hand2", command=lambda: toggle_preview()
    )
    preview_button.place(relx=0.65, rely=0.78, relwidth=0.2, relheight=0.04)
    ToolTip(preview_button, _("Show/hide a preview of the processed output"))

    # --- Camera Selection ---
    camera_label = ctk.CTkLabel(root, text=_("Select Camera:"))
    camera_label.place(relx=0.1, rely=0.83, relwidth=0.2, relheight=0.03)

    available_cameras = get_available_cameras()
    camera_indices, camera_names = available_cameras

    if not camera_names or camera_names[0] == "No cameras found":
        camera_variable = ctk.StringVar(value="No cameras found")
        camera_optionmenu = ctk.CTkOptionMenu(
            root,
            variable=camera_variable,
            values=["No cameras found"],
            state="disabled",
        )
    else:
        camera_variable = ctk.StringVar(value=camera_names[0])
        camera_optionmenu = ctk.CTkOptionMenu(
            root, variable=camera_variable, values=camera_names
        )

    camera_optionmenu.place(relx=0.35, rely=0.83, relwidth=0.25, relheight=0.03)
    ToolTip(camera_optionmenu, _("Select which camera to use for live mode"))

    live_button = ctk.CTkButton(
        root,
        text=_("Live"),
        cursor="hand2",
        command=lambda: webcam_preview(
            root,
            (
                camera_indices[camera_names.index(camera_variable.get())]
                if camera_names and camera_names[0] != "No cameras found"
                else None
            ),
        ),
        state=(
            "normal"
            if camera_names and camera_names[0] != "No cameras found"
            else "disabled"
        ),
    )
    live_button.place(relx=0.65, rely=0.83, relwidth=0.2, relheight=0.03)
    ToolTip(live_button, _("Start real-time face swap using webcam"))
    # --- End Camera Selection ---

    # --- Face Enhancer Dropdown ---
    enhancer_options = ["None", "GFPGAN", "GPEN-512", "GPEN-256"]
    enhancer_key_map = {
        "None": None,
        "GFPGAN": "face_enhancer",
        "GPEN-512": "face_enhancer_gpen512",
        "GPEN-256": "face_enhancer_gpen256",
    }

    # Determine initial value from current fp_ui state
    initial_enhancer = "None"
    if modules.globals.fp_ui.get("face_enhancer", False):
        initial_enhancer = "GFPGAN"
    elif modules.globals.fp_ui.get("face_enhancer_gpen512", False):
        initial_enhancer = "GPEN-512"
    elif modules.globals.fp_ui.get("face_enhancer_gpen256", False):
        initial_enhancer = "GPEN-256"

    enhancer_variable = ctk.StringVar(value=initial_enhancer)

    def on_enhancer_change(choice: str):
        # Disable all enhancers first
        for key in ["face_enhancer", "face_enhancer_gpen256", "face_enhancer_gpen512"]:
            update_tumbler(key, False)
        # Enable the selected one
        selected_key = enhancer_key_map.get(choice)
        if selected_key:
            update_tumbler(selected_key, True)
        save_switch_states()

    enhancer_label = ctk.CTkLabel(root, text="Face Enhancer:")
    enhancer_label.place(relx=0.1, rely=0.62, relwidth=0.2, relheight=0.03)

    enhancer_dropdown = ctk.CTkOptionMenu(
        root,
        variable=enhancer_variable,
        values=enhancer_options,
        command=on_enhancer_change,
    )
    enhancer_dropdown.place(relx=0.35, rely=0.62, relwidth=0.3, relheight=0.03)
    ToolTip(enhancer_dropdown, _("Select a face enhancement model (None = no enhancement)"))

    # 1) Define a DoubleVar for transparency (0 = fully transparent, 1 = fully opaque)
    transparency_var = ctk.DoubleVar(value=1.0)

    def on_transparency_change(value: float):
        # Convert slider value to float
        val = float(value)
        modules.globals.opacity = val  # Set global opacity
        percentage = int(val * 100)

        if percentage == 0:
            modules.globals.fp_ui["face_enhancer"] = False
            update_status("Transparency set to 0% - Face swapping disabled.")
        elif percentage == 100:
            modules.globals.face_swapper_enabled = True
            update_status("Transparency set to 100%.")
        else:
            modules.globals.face_swapper_enabled = True
            update_status(f"Transparency set to {percentage}%")

    # 2) Transparency label and slider
    transparency_label = ctk.CTkLabel(root, text="Transparency:")
    transparency_label.place(relx=0.15, rely=0.66, relwidth=0.2, relheight=0.03)

    transparency_slider = ctk.CTkSlider(
        root,
        from_=0.0,
        to=1.0,
        variable=transparency_var,
        command=on_transparency_change,
        fg_color="#E0E0E0",
        progress_color="#007BFF",
        button_color="#FFFFFF",
        button_hover_color="#CCCCCC",
        height=5,
        border_width=1,
        corner_radius=3,
    )
    transparency_slider.place(relx=0.35, rely=0.67, relwidth=0.5, relheight=0.02)
    ToolTip(transparency_slider, _("Blend between original and swapped face (0% = original, 100% = fully swapped)"))

    # 3) Sharpness label & slider
    sharpness_var = ctk.DoubleVar(value=0.0)  # start at 0.0
    def on_sharpness_change(value: float):
        modules.globals.sharpness = float(value)
        update_status(f"Sharpness set to {value:.1f}")

    sharpness_label = ctk.CTkLabel(root, text="Sharpness:")
    sharpness_label.place(relx=0.15, rely=0.69, relwidth=0.2, relheight=0.03)

    sharpness_slider = ctk.CTkSlider(
        root,
        from_=0.0,
        to=5.0,
        variable=sharpness_var,
        command=on_sharpness_change,
        fg_color="#E0E0E0",
        progress_color="#007BFF",
        button_color="#FFFFFF",
        button_hover_color="#CCCCCC",
        height=5,
        border_width=1,
        corner_radius=3,
    )
    sharpness_slider.place(relx=0.35, rely=0.70, relwidth=0.5, relheight=0.02)
    ToolTip(sharpness_slider, _("Sharpen the enhanced face output"))

    # 4) Mouth Mask Size slider
    mouth_mask_size_var = ctk.DoubleVar(value=modules.globals.mouth_mask_size)

    def on_mouth_mask_size_change(value: float):
        val = float(value)
        modules.globals.mouth_mask_size = val
        # Auto-enable/disable mouth mask based on slider position
        if val > 0:
            modules.globals.mouth_mask = True
            mouth_mask_var.set(True)
        else:
            modules.globals.mouth_mask = False
            mouth_mask_var.set(False)
            modules.globals.show_mouth_mask_box = False

    def on_mouth_mask_slider_release(event):
        # Hide bounding box when user releases the slider
        modules.globals.show_mouth_mask_box = False

    def on_mouth_mask_slider_press(event):
        # Show bounding box while dragging
        if modules.globals.mouth_mask_size > 0:
            modules.globals.show_mouth_mask_box = True

    mouth_mask_size_label = ctk.CTkLabel(root, text="Mouth Mask:")
    mouth_mask_size_label.place(relx=0.15, rely=0.72, relwidth=0.2, relheight=0.03)

    mouth_mask_size_slider = ctk.CTkSlider(
        root,
        from_=0.0,
        to=100.0,
        variable=mouth_mask_size_var,
        command=on_mouth_mask_size_change,
        fg_color="#E0E0E0",
        progress_color="#007BFF",
        button_color="#FFFFFF",
        button_hover_color="#CCCCCC",
        height=5,
        border_width=1,
        corner_radius=3,
    )
    mouth_mask_size_slider.place(relx=0.35, rely=0.73, relwidth=0.5, relheight=0.02)
    mouth_mask_size_slider.bind("<ButtonPress-1>", on_mouth_mask_slider_press)
    mouth_mask_size_slider.bind("<ButtonRelease-1>", on_mouth_mask_slider_release)
    ToolTip(mouth_mask_size_slider, _("0 = use swapped mouth, 100 = expose original mouth to chin area"))

    # Status and link at the bottom
    global status_label
    status_label = ctk.CTkLabel(root, text=None, justify="center")
    status_label.place(relx=0.1, rely=0.75, relwidth=0.8)

    donate_label = ctk.CTkLabel(
        root, text="Deep Live Cam", justify="center", cursor="hand2"
    )
    donate_label.place(relx=0.1, rely=0.87, relwidth=0.8)
    donate_label.configure(
        text_color=ctk.ThemeManager.theme.get("URL").get("text_color")
    )
    donate_label.bind(
        "<Button>", lambda event: webbrowser.open("https://deeplivecam.net")
    )

    return root