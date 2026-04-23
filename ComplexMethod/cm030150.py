def main():
    opts, args = parse_args()

    if getattr(opts, 'pid', None) is not None:
        try:
            attach(opts.pid, opts.commands)
        except RuntimeError:
            print(
                f"Cannot attach to pid {opts.pid}, please make sure that the process exists "
                "and is using the same Python version."
            )
            sys.exit(1)
        except PermissionError:
            exit_with_permission_help_text()
        return
    elif getattr(opts, 'module', None) is not None:
        file = opts.module
        target = _ModuleTarget(file)
    else:
        file = args.pop(0)
        if file.endswith('.pyz'):
            target = _ZipTarget(file)
        else:
            target = _ScriptTarget(file)

    sys.argv[:] = [file] + args  # Hide "pdb.py" and pdb options from argument list

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. There is a "restart" command
    # which allows explicit specification of command line arguments.
    pdb = Pdb(mode='cli', backend='monitoring', colorize=True)
    pdb.rcLines.extend(opts.commands)
    while True:
        try:
            pdb._run(target)
        except Restart:
            print("Restarting", target, "with arguments:")
            print("\t" + " ".join(sys.argv[1:]))
        except SystemExit as e:
            # In most cases SystemExit does not warrant a post-mortem session.
            print("The program exited via sys.exit(). Exit status:", end=' ')
            print(e)
        except BaseException as e:
            traceback.print_exception(e, colorize=_colorize.can_colorize())
            print("Uncaught exception. Entering post mortem debugging")
            print("Running 'cont' or 'step' will restart the program")
            try:
                pdb.interaction(None, e)
            except Restart:
                print("Restarting", target, "with arguments:")
                print("\t" + " ".join(sys.argv[1:]))
                continue
        if pdb._user_requested_quit:
            break
        print("The program finished and will be restarted")