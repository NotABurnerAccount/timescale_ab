from typing import List, Tuple
from time import time

import psycopg


def execute_benchmark_with_connection_parameters(
    connection_string: str, params: List[List[str]]
) -> List[Tuple[Tuple[float, float], float]]:
    """Creates a connection to use for the list of query params

    Creates a connection to the database with the provided connection
    string and executes a query for each of the query param lists provided.
    The creation of the connection is done here to allow for the
    execute_bechmark function to recieve a cursor from a distinct connection
    in multithreading or multiprocessing scenarios. The psycopg docs located
    at https://www.psycopg.org/psycopg3/docs/api/cursors.html#cursor-classes
    discuss that cursors from the same connection cannot execute in parallel.

    Parameters
    ----------
    connection_string: str
        A postgresql connection string like postgresql://user:pass@host:port/db
    params: List[List[str]]
        Query parameters to use

    Returns
    -------
    List[Tuple[Tuple[float, float], float]]
        The results of all the queries along with their processing time
    """
    with psycopg.connect(conninfo=connection_string) as db_connection:
        return execute_benchmark(db_connection.cursor(), params)


def execute_benchmark(
    cursor: psycopg.Cursor, params: List[List[str]]
) -> List[Tuple[Tuple[float, float], float]]:
    """Executes the benchmark query with the parameters

    Executes the benchmark query with each set of query parameters
    sequentially and provides the caller with the result of the query and
    the processing time of the query.

    Parameters
    ----------
    cursor: psycopg.Cursor
        Cursor to execute queries with
    params: List[List[str]]
        List of query parameters to use

    Returns
    -------
    List[Tuple[Tuple[float, float], float]]
        The results of all the queries along with their processing time
    """
    query = """
    SELECT min(usage), max(usage) from cpu_usage 
    WHERE host = %(host)s
    AND ts > %(begin)s
    AND ts < %(end)s
    GROUP BY time_bucket('1 minute', ts, %(begin)s);
    """

    def single_query(param_set):
        named_params = {
            name: param for name, param in zip(("host", "begin", "end"), param_set)
        }
        start_time = time()
        cursor.execute(query, named_params)
        results = cursor.fetchall()
        end_time = time()
        total_time = end_time - start_time
        return (results, total_time)

    return list(map(single_query, params))
