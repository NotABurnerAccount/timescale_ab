from multiprocessing.pool import Pool
from operator import itemgetter
from functools import partial
from itertools import chain
from typing import List
import subprocess

from timescale_ab.load_data import (
    load_lines_from_file,
    load_tuples_from_lines,
    group_rows_by_field,
    group_data_for_runners,
)
from timescale_ab.query import execute_benchmark_with_connection_parameters
from timescale_ab.reporter import report


def bootstrap_container(container_runner: str) -> None:
    """Run timescaledb in a container

    Use the specified container runner (docker,podman) to run a container
    with timescaledb

    Parameters
    ----------
    container_runner: str
        Should be either podman or docker
    """

    db_start = subprocess.run(
        [
            f"{container_runner} run --name benchmark-container -dit --rm -e POSTGRES_PASSWORD=password -p 5432:5432 timescale/timescaledb:latest-pg14-oss"
        ],
        shell=True,
    )
    if db_start.returncode != 0:
        raise Exception("Unable to start timescaledb container")
    db_ready = False
    while not db_ready:
        check_db_ready = subprocess.run(
            [f"{container_runner} exec benchmark-container pg_isready -h localhost"],
            shell=True,
        )
        db_ready = check_db_ready.returncode == 0


def prepare_database() -> None:
    """Prepare the database for the benchmark

    Prepares the database for the benchmark by creating the necessary
    table and populating it with the information in the embedded csv.
    """

    # data directory is a sibling of this file
    path_to_file = __file__.split("/")[:-1]
    sql_path = "/".join(path_to_file + ["data/cpu_usage.sql"])

    # first create the database and hypertable
    create_result = subprocess.run(
        [f"psql -h localhost -U postgres < {sql_path}"],
        env={"PGPASSWORD": "password"},
        shell=True,
    )

    if create_result.returncode != 0:
        raise Exception("Unable to create database or table")

    csv_path = "/".join(path_to_file + ["data/cpu_usage.csv"])
    # populate the table
    populate_result = subprocess.run(
        [
            f'psql -h localhost -U postgres -d homework -c "\COPY cpu_usage FROM {csv_path} CSV HEADER"'
        ],
        env={"PGPASSWORD": "password"},
        shell=True,
    )
    if populate_result.returncode != 0:
        raise Exception("Unable to populate table")


def load_file_to_runner_grouped_data(
    file_path: str, have_header: bool = True, group_by: int = 0, runners: int = 1
) -> List[List[List[str]]]:
    """Loads a csv file into runner grouped query params.

    Composes several functions to load a csv file into grouped runner query
    parameters.

    Parameters
    ----------
    file_name : str
        Path to the file
    have_header : bool
        Whether these lines start with a header
    index : int
        The index number to group by
    runners : int
        Count of runners to group data for should be greater than 0

    Returns
    -------
    List[List[List[str]]]
    """
    lines = load_lines_from_file(file_path)
    rows = load_tuples_from_lines(lines, have_header)
    field_grouped_data = group_rows_by_field(rows, group_by)
    runner_grouped_data = group_data_for_runners(field_grouped_data, runners)
    return runner_grouped_data


def cleanup_container(container_runner: str) -> None:
    """Cleanup the benchmark-container

    Using the provided container_runner usually podman or docker kill the
    benchmark-container or raise an Exception if that fails.

    Parameters
    ----------
    container_runner: str
        Container running software to use when killing the container.
        Should be the same used to start the container.
    """
    cleanup_result = subprocess.run(
        [f"{container_runner} kill benchmark-container"], shell=True
    )
    if cleanup_result.returncode != 0:
        raise Exception("Unable to cleanup container")


def run(
    file_path: str,
    runners: int,
    start_option: str,
    connection_string: str = None,
    container_runner: str = None,
    cleanup: bool = False,
) -> None:
    """ Run the tsab application

    This is the primary entrypoint to the tsab application after the cli
    which should parse the users arguments and send them to this function.

    Parameters
    ----------
    file_path: str
        Path the query parameter file to use. We assume it has a header
        and discard the header. A user should notice this as the count of
        queries executed will be different from the number of lines in
        their file.
    runners: int
        Number of concurrent runners to use
    start_option: str
        Whether to user containers or not. When using container as the 
        start_option the application will bootstrap and populate a database
        in the container software of choice
    container_runner: str
        The container runner software to be used if start_option = container
        Expected to be one of podman or docker but not explicitly checked
        to allow for other compatible software if a user believes it will
        work.
    cleanup: bool
        Whether or not to cleanup the container that is bootstrap for a
        run of this software with containers.
    """
    try:
        if start_option == "container":
            bootstrap_container(container_runner)
            prepare_database()
            connection_string = "postgresql://postgres:password@localhost:5432/homework"

        runner_grouped_data = load_file_to_runner_grouped_data(
            file_path, runners=runners
        )
        benchmark_function = partial(
            execute_benchmark_with_connection_parameters, connection_string
        )
        # Uses parallelism since distict runners are required
        with Pool(runners) as pool:
            results_with_time = list(
                chain.from_iterable(
                    pool.imap_unordered(benchmark_function, runner_grouped_data)
                )
            )

        query_times = list(map(itemgetter(1), results_with_time))
        print(report(query_times))
    finally:
        if cleanup and start_option == "container":
            cleanup_container(container_runner)
