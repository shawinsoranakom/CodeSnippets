def main(args):
    try:
        if args.build_tgz:
            _prepare_build_dir(args)
            docker_tgz = DockerTgz(args)
            docker_tgz.build()
            try:
                docker_tgz.start_test()
                published_files = publish(args, 'tgz', ['tar.gz', 'zip'])
            except Exception as e:
                logging.error("Won't publish the tgz release.\n Exception: %s" % str(e))
        if args.build_rpm:
            _prepare_build_dir(args)
            docker_rpm = DockerRpm(args)
            docker_rpm.build()
            try:
                docker_rpm.start_test()
                published_files = publish(args, 'rpm', ['rpm'])
                if args.sign:
                    logging.info('Signing rpm package')
                    rpm_sign(args, published_files[0])
                    logging.info('Generate rpm repo')
                    docker_rpm.gen_rpm_repo(args, published_files[0])
            except Exception as e:
                logging.error("Won't publish the rpm release.\n Exception: %s" % str(e))
        if args.build_deb:
            _prepare_build_dir(args, move_addons=False)
            docker_deb = DockerDeb(args)
            docker_deb.build()
            try:
                docker_deb.start_test()
                published_files = publish(args, 'deb', ['deb', 'dsc', 'changes', 'tar.xz'])
                gen_deb_package(args, published_files)
            except Exception as e:
                logging.error("Won't publish the deb release.\n Exception: %s" % str(e))
        if args.build_win:
            _prepare_build_dir(args, win32=True)
            docker_wine = DockerWine(args)
            docker_wine.build()
            try:
                published_files = publish(args, 'windows', ['exe'])
            except Exception as e:
                logging.error("Won't publish the exe release.\n Exception: %s" % str(e))
        if args.build_iot:
            _prepare_build_dir(args, win32=True)
            docker_iot = DockerIot(args)
            docker_iot.build()
            try:
                published_files = publish(args, 'iot', ['exe'])
            except Exception as e:
                logging.error("Won't publish the iot release.\n Exception: %s" % str(e))
    except Exception as e:
        logging.error('Something bad happened ! : {}'.format(e))
        traceback.print_exc()
    finally:
        if args.no_remove:
            logging.info('Build dir "{}" not removed'.format(args.build_dir))
        else:
            if os.path.exists(args.build_dir):
                shutil.rmtree(args.build_dir)
                logging.info('Build dir %s removed' % args.build_dir)