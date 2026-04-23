def main():
    # sys.argv[1] contains the command (sft/dpo/rm/train), sys.argv[2:] contains the rest args
    command = sys.argv[1] if len(sys.argv) > 1 else "sft"

    # Routing needs the sub-command, but downstream trainers usually expect argv without it.
    if command in _DIST_TRAIN_COMMANDS:
        sys.argv.pop(1)
    else:
        # Backward-compat: if someone runs `torchrun launcher.py config.yaml`,
        # treat it as sft by default.
        if len(sys.argv) > 1 and sys.argv[1].endswith((".yaml", ".yml")):
            command = "sft"
    if command in ("train", "sft"):
        from llamafactory.v1.trainers.sft_trainer import run_sft

        run_sft()
    elif command == "dpo":
        # from llamafactory.v1.trainers.dpo_trainer import run_dpo
        # run_dpo()
        raise NotImplementedError("DPO trainer is not implemented yet.")
    elif command == "rm":
        # from llamafactory.v1.trainers.rm_trainer import run_rm
        # run_rm()
        raise NotImplementedError("RM trainer is not implemented yet.")