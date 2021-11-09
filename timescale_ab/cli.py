from argparse import ArgumentParser

from timescale_ab.run import run


def generate_parser():
    parser = ArgumentParser(description="Like apache bench but for timescale.")
    parent_parser = ArgumentParser()
    parent_parser.add_argument(
        "file_path",
        type=str,
        help="Path to file of query params to use for benchmarking",
    )
    parent_parser.add_argument(
        "--runners",
        type=int,
        default=10,
        help="Number of concurrent runners to use for benchmarks (default 10)",
    )
    db_start_options = parser.add_subparsers(
        title="start option", dest="start_option", required=True
    )
    # parser for running in a container
    container_parser = db_start_options.add_parser(
        "container",
        help="run tsdb in a container before running the benchmark",
        parents=[parent_parser],
        conflict_handler="resolve",
    )
    container_parser.add_argument(
        "container_runner",
        choices=["docker", "podman"],
        help="Contianer software to start database with",
    )
    container_parser.add_argument(
        "--cleanup",
        action="store_true",
        help="After running the benchmark remove the running container",
    )

    # parser for running with an existing tsdb
    existing_parser = db_start_options.add_parser(
        "existing",
        help="run benchmark against an already running database",
        parents=[parent_parser],
        conflict_handler="resolve",
    )
    existing_parser.add_argument(
        "--connection-string",
        type=str,
        default="postgresql://postgres:password@localhost:5432/homework",
        help="Connection string to connect to the existing database (default postgresql://postgres:password@localhost:5432/homework)",
    )

    return parser


def main():
    return run(**vars(generate_parser().parse_args()))
