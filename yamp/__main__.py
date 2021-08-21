import argparse
import pathlib

from yamp import print_library


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "library",
        nargs="?",
        help="the library to document",
    )
    parser.add_argument("--out", default="docs/api", help="where to dump the docs")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.set_defaults(verbose=False)
    args = parser.parse_args()
    print_library(
        library=args.library, output_dir=pathlib.Path(args.out), verbose=args.verbose
    )


if __name__ == "__main__":
    main()
