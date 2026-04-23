def __init__(self, flist=None, filename=None, key=None, root=None):
        # Delay import: runscript imports pyshell imports EditorWindow.
        from idlelib.runscript import ScriptBinding

        if EditorWindow.help_url is None:
            EditorWindow.help_url = _get_dochome()
        self.flist = flist
        root = root or flist.root
        self.root = root
        self.menubar = Menu(root)
        self.top = top = window.ListedToplevel(root, menu=self.menubar)
        if flist:
            self.tkinter_vars = flist.vars
            #self.top.instance_dict makes flist.inversedict available to
            #configdialog.py so it can access all EditorWindow instances
            self.top.instance_dict = flist.inversedict
        else:
            self.tkinter_vars = {}  # keys: Tkinter event names
                                    # values: Tkinter variable instances
            self.top.instance_dict = {}
        self.recent_files_path = idleConf.userdir and os.path.join(
                idleConf.userdir, 'recent-files.lst')

        self.prompt_last_line = ''  # Override in PyShell
        self.text_frame = text_frame = Frame(top)
        self.vbar = vbar = Scrollbar(text_frame, name='vbar')
        width = idleConf.GetOption('main', 'EditorWindow', 'width', type='int')
        text_options = {
                'name': 'text',
                'padx': 5,
                'wrap': 'none',
                'highlightthickness': 0,
                'width': width,
                'tabstyle': 'wordprocessor',  # new in 8.5
                'height': idleConf.GetOption(
                        'main', 'EditorWindow', 'height', type='int'),
                }
        self.text = text = MultiCallCreator(Text)(text_frame, **text_options)
        self.top.focused_widget = self.text

        self.createmenubar()
        self.apply_bindings()

        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<<close-window>>", self.close_event)
        if macosx.isAquaTk():
            # Command-W on editor windows doesn't work without this.
            text.bind('<<close-window>>', self.close_event)
            # Some OS X systems have only one mouse button, so use
            # control-click for popup context menus there. For two
            # buttons, AquaTk defines <2> as the right button, not <3>.
            text.bind("<Control-Button-1>",self.right_menu_event)
            text.bind("<2>", self.right_menu_event)
        else:
            # Elsewhere, use right-click for popup menus.
            text.bind("<3>",self.right_menu_event)

        text.bind('<MouseWheel>', wheel_event)
        if text._windowingsystem == 'x11':
            text.bind('<Button-4>', wheel_event)
            text.bind('<Button-5>', wheel_event)
        text.bind('<Configure>', self.handle_winconfig)
        text.bind("<<cut>>", self.cut)
        text.bind("<<copy>>", self.copy)
        text.bind("<<paste>>", self.paste)
        text.bind("<<center-insert>>", self.center_insert_event)
        text.bind("<<help>>", self.help_dialog)
        text.bind("<<python-docs>>", self.python_docs)
        text.bind("<<about-idle>>", self.about_dialog)
        text.bind("<<open-config-dialog>>", self.config_dialog)
        text.bind("<<open-module>>", self.open_module_event)
        text.bind("<<do-nothing>>", lambda event: "break")
        text.bind("<<select-all>>", self.select_all)
        text.bind("<<remove-selection>>", self.remove_selection)
        text.bind("<<find>>", self.find_event)
        text.bind("<<find-again>>", self.find_again_event)
        text.bind("<<find-in-files>>", self.find_in_files_event)
        text.bind("<<find-selection>>", self.find_selection_event)
        text.bind("<<replace>>", self.replace_event)
        text.bind("<<goto-line>>", self.goto_line_event)
        text.bind("<<smart-backspace>>",self.smart_backspace_event)
        text.bind("<<newline-and-indent>>",self.newline_and_indent_event)
        text.bind("<<smart-indent>>",self.smart_indent_event)
        self.fregion = fregion = self.FormatRegion(self)
        # self.fregion used in smart_indent_event to access indent_region.
        text.bind("<<indent-region>>", fregion.indent_region_event)
        text.bind("<<dedent-region>>", fregion.dedent_region_event)
        text.bind("<<comment-region>>", fregion.comment_region_event)
        text.bind("<<uncomment-region>>", fregion.uncomment_region_event)
        text.bind("<<tabify-region>>", fregion.tabify_region_event)
        text.bind("<<untabify-region>>", fregion.untabify_region_event)
        indents = self.Indents(self)
        text.bind("<<toggle-tabs>>", indents.toggle_tabs_event)
        text.bind("<<change-indentwidth>>", indents.change_indentwidth_event)
        text.bind("<Left>", self.move_at_edge_if_selection(0))
        text.bind("<Right>", self.move_at_edge_if_selection(1))
        text.bind("<<del-word-left>>", self.del_word_left)
        text.bind("<<del-word-right>>", self.del_word_right)
        text.bind("<<beginning-of-line>>", self.home_callback)

        if flist:
            flist.inversedict[self] = key
            if key:
                flist.dict[key] = self
            text.bind("<<open-new-window>>", self.new_callback)
            text.bind("<<close-all-windows>>", self.flist.close_all_callback)
            text.bind("<<open-class-browser>>", self.open_module_browser)
            text.bind("<<open-path-browser>>", self.open_path_browser)
            text.bind("<<open-turtle-demo>>", self.open_turtle_demo)

        self.set_status_bar()
        text_frame.pack(side=LEFT, fill=BOTH, expand=1)
        text_frame.rowconfigure(1, weight=1)
        text_frame.columnconfigure(1, weight=1)
        vbar['command'] = self.handle_yview
        vbar.grid(row=1, column=2, sticky=NSEW)
        text['yscrollcommand'] = vbar.set
        text['font'] = idleConf.GetFont(self.root, 'main', 'EditorWindow')
        text.grid(row=1, column=1, sticky=NSEW)
        text.focus_set()
        self.set_width()

        # usetabs true  -> literal tab characters are used by indent and
        #                  dedent cmds, possibly mixed with spaces if
        #                  indentwidth is not a multiple of tabwidth,
        #                  which will cause Tabnanny to nag!
        #         false -> tab characters are converted to spaces by indent
        #                  and dedent cmds, and ditto TAB keystrokes
        # Although use-spaces=0 can be configured manually in config-main.def,
        # configuration of tabs v. spaces is not supported in the configuration
        # dialog.  IDLE promotes the preferred Python indentation: use spaces!
        usespaces = idleConf.GetOption('main', 'Indent',
                                       'use-spaces', type='bool')
        self.usetabs = not usespaces

        # tabwidth is the display width of a literal tab character.
        # CAUTION:  telling Tk to use anything other than its default
        # tab setting causes it to use an entirely different tabbing algorithm,
        # treating tab stops as fixed distances from the left margin.
        # Nobody expects this, so for now tabwidth should never be changed.
        self.tabwidth = 8    # must remain 8 until Tk is fixed.

        # indentwidth is the number of screen characters per indent level.
        # The recommended Python indentation is four spaces.
        self.indentwidth = self.tabwidth
        self.set_notabs_indentwidth()

        # Store the current value of the insertofftime now so we can restore
        # it if needed.
        if not hasattr(idleConf, 'blink_off_time'):
            idleConf.blink_off_time = self.text['insertofftime']
        self.update_cursor_blink()

        # When searching backwards for a reliable place to begin parsing,
        # first start num_context_lines[0] lines back, then
        # num_context_lines[1] lines back if that didn't work, and so on.
        # The last value should be huge (larger than the # of lines in a
        # conceivable file).
        # Making the initial values larger slows things down more often.
        self.num_context_lines = 50, 500, 5000000
        self.per = per = self.Percolator(text)
        self.undo = undo = self.UndoDelegator()
        per.insertfilter(undo)
        text.undo_block_start = undo.undo_block_start
        text.undo_block_stop = undo.undo_block_stop
        undo.set_saved_change_hook(self.saved_change_hook)
        # IOBinding implements file I/O and printing functionality
        self.io = io = self.IOBinding(self)
        io.set_filename_change_hook(self.filename_change_hook)
        self.good_load = False
        self.set_indentation_params(False)
        self.color = None # initialized below in self.ResetColorizer
        self.code_context = None # optionally initialized later below
        self.line_numbers = None # optionally initialized later below
        if filename:
            if os.path.exists(filename) and not os.path.isdir(filename):
                if io.loadfile(filename):
                    self.good_load = True
                    is_py_src = self.ispythonsource(filename)
                    self.set_indentation_params(is_py_src)
            else:
                io.set_filename(filename)
                self.good_load = True

        self.ResetColorizer()
        self.saved_change_hook()
        self.update_recent_files_list()
        self.load_extensions()
        menu = self.menudict.get('window')
        if menu:
            end = menu.index("end")
            if end is None:
                end = -1
            if end >= 0:
                menu.add_separator()
                end = end + 1
            self.wmenu_end = end
            window.register_callback(self.postwindowsmenu)

        # Some abstractions so IDLE extensions are cross-IDE
        self.askinteger = simpledialog.askinteger
        self.askyesno = messagebox.askyesno
        self.showerror = messagebox.showerror

        # Add pseudoevents for former extension fixed keys.
        # (This probably needs to be done once in the process.)
        text.event_add('<<autocomplete>>', '<Key-Tab>')
        text.event_add('<<try-open-completions>>', '<KeyRelease-period>',
                       '<KeyRelease-slash>', '<KeyRelease-backslash>')
        text.event_add('<<try-open-calltip>>', '<KeyRelease-parenleft>')
        text.event_add('<<refresh-calltip>>', '<KeyRelease-parenright>')
        text.event_add('<<paren-closed>>', '<KeyRelease-parenright>',
                       '<KeyRelease-bracketright>', '<KeyRelease-braceright>')

        # Former extension bindings depends on frame.text being packed
        # (called from self.ResetColorizer()).
        autocomplete = self.AutoComplete(self, self.user_input_insert_tags)
        text.bind("<<autocomplete>>", autocomplete.autocomplete_event)
        text.bind("<<try-open-completions>>",
                  autocomplete.try_open_completions_event)
        text.bind("<<force-open-completions>>",
                  autocomplete.force_open_completions_event)
        text.bind("<<expand-word>>", self.AutoExpand(self).expand_word_event)
        text.bind("<<format-paragraph>>",
                  self.FormatParagraph(self).format_paragraph_event)
        parenmatch = self.ParenMatch(self)
        text.bind("<<flash-paren>>", parenmatch.flash_paren_event)
        text.bind("<<paren-closed>>", parenmatch.paren_closed_event)
        scriptbinding = ScriptBinding(self)
        text.bind("<<check-module>>", scriptbinding.check_module_event)
        text.bind("<<run-module>>", scriptbinding.run_module_event)
        text.bind("<<run-custom>>", scriptbinding.run_custom_event)
        text.bind("<<do-rstrip>>", self.Rstrip(self).do_rstrip)
        self.ctip = ctip = self.Calltip(self)
        text.bind("<<try-open-calltip>>", ctip.try_open_calltip_event)
        #refresh-calltip must come after paren-closed to work right
        text.bind("<<refresh-calltip>>", ctip.refresh_calltip_event)
        text.bind("<<force-open-calltip>>", ctip.force_open_calltip_event)
        text.bind("<<zoom-height>>", self.ZoomHeight(self).zoom_height_event)
        if self.allow_code_context:
            self.code_context = self.CodeContext(self)
            text.bind("<<toggle-code-context>>",
                      self.code_context.toggle_code_context_event)
        else:
            self.update_menu_state('options', '*ode*ontext', 'disabled')
        if self.allow_line_numbers:
            self.line_numbers = self.LineNumbers(self)
            if idleConf.GetOption('main', 'EditorWindow',
                                  'line-numbers-default', type='bool'):
                self.toggle_line_numbers_event()
            text.bind("<<toggle-line-numbers>>", self.toggle_line_numbers_event)
        else:
            self.update_menu_state('options', '*ine*umbers', 'disabled')

        self.mtime = self.last_mtime()
        text_frame.bind('<FocusIn>', self.focus_in_event)