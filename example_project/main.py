import argparse
import json
import sys

import numpy
import zmq


def main():
    print(
        json.dumps(
            {
                "python": sys.version.split(" ")[0],
                "numpy": numpy.__version__,
                "pyzmq": zmq.__version__,
            }
        )
    )


def retval():
    parser = argparse.ArgumentParser(description="Change the return value of the program")
    parser.add_argument(
        "--zero",
        action="store_true",
        help="Setting this arg will force the return value to 0",
    )
    args = parser.parse_args()
    sys.exit(0 if args.zero else 255)


if __name__ == "__main__":
    main()
