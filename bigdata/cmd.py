import argparse
import os
import re
from .profile import Profiler


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


def run(args):
    args.profile = args.profile or args.dump or args.runsnake

    __import__("bigdata.suites." + args.suite)

    Profiler(args).run()


if __name__ == '__main__':
    main()
