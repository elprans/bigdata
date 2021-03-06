import argparse
import os
import re
from . import setup_db

def main():

    parser = argparse.ArgumentParser("python -m  bigdata.cmd")

    parser.add_argument(
        '--dburl', type=str,
        default="postgresql://scott:tiger@localhost/test",
        help="database URL, default sqlite:///profile.db"
    )
    parser.add_argument(
        '--echo', action='store_true',
        help="Echo SQL output")

    subparsers = parser.add_subparsers()
    subparser = subparsers.add_parser(
        "run",
        help="run a suite")
    subparser.set_defaults(cmd=run)

    subparser.add_argument(
        "suite", type=str,
        help="suite name"
    )

    subparser.add_argument(
        "--test", type=str,
        help="run specific test name"
    )

    subparser.add_argument(
        "--poolsize", type=int,
        default=15,
        help="number of workers/connections to use"
    )
    subparser.add_argument(
        "--directory", type=str,
        help="Directory location where datafiles are"
    )
    subparser.add_argument(
        "--no-autocommit", action="store_true",
        help="disable autocommit, if possible (only with threaded)"
    )

    subparser.add_argument(
        "--allow-executemany", action="store_true",
        help="allow the use of executemany, only possible with threaded"
    )

    subparser.add_argument(
        '--profile', action='store_true',
        help='run profiling and dump call counts')
    subparser.add_argument(
        '--dump', action='store_true',
        help='dump full call profile (implies --profile)')
    subparser.add_argument(
        '--runsnake', action='store_true',
        help='invoke runsnakerun (implies --profile)')

    subparser = subparsers.add_parser(
        "list",
        help="list suites")
    subparser.set_defaults(cmd=list_)

    subparser = subparsers.add_parser(
        "rebuild",
        help="rebuild the test DB from scratch")
    subparser.set_defaults(cmd=rebuild)

    args = parser.parse_args()
    if not hasattr(args, "cmd"):
        parser.error("too few arguments")
    fn = args.cmd
    fn(args)


def list_(args):
    suites = []
    for file_ in os.listdir(os.path.join(os.path.dirname(__file__), "suites")):
        match = re.match(r'^([a-z].*).py$', file_)
        if match:
            suites.append(match.group(1))
    print("\n".join(suites))


def rebuild(args):
    setup_db.setup_database(args, drop=True)


def run(args):

    _temp = __import__(
        "bigdata.suites." + args.suite, fromlist=['run_test', 'setup'])
    run_test, setup = _temp.run_test, _temp.setup
    setup_db.setup_database(args)
    setup_db.clear_data(args)
    setup(args)
    run_test()

if __name__ == '__main__':
    main()
