from typing import Iterable, List, Dict
from collections import defaultdict
from itertools import islice


def load_lines_from_file(file_name: str):
    """Loads stripped lines from a file

    Parameters
    ----------
    file_name : str
        Path to the file

    Yields
    ------
    line : str
        Stripped line from the file
    """
    with open(file_name) as file_handle:
        yield from map(str.strip, file_handle)


def load_tuples_from_lines(csv_lines: Iterable[str], have_header: bool = True):
    """Loads 'tuples' from csv lines

    This loads tuples from the csv lines that it recieves, and ignores the
    first line when have_header is set. Although it says tuples, this
    yields List[str] instead because that's what split generates and this
    function means tuple like row.

    Parameters
    ----------
    csv_lines : Iterable[str]
        Lines to load into tuples
    have_header : bool
        Whether these lines start with a header

    Yields
    ------
    row : List[str]
        A tuple from the csv
    """
    # this is fun (bool is 0 or 1), there are cleaner ways to do this like an if
    for line in islice(csv_lines, have_header, None):
        yield line.split(",")


def group_rows_by_field(
    rows: Iterable[List[str]], index: int = 0
) -> Dict[str, List[List[str]]]:
    """Group rows by a field.

    Groups rows by an index such that all rows with the same value for the
    selected index number will be grouped into the same entry of a dict.

    Parameters
    ----------
    rows : Iterable[List[str]]
        Rows to group
    index : int
        The index number to group by

    Returns
    -------
    Dict[str, List[List[str]]]
    """
    result = defaultdict(list)
    for row in rows:
        result[row[index]].append(row)
    return result


def group_data_for_runners(
    groups: Dict[str, List[str]], runners: int = 1
) -> List[List[List[str]]]:
    """Group row groups into runner number of buckets

    Groups rows which have been grouped by another field into runner
    number of groups so that number of runners can process those rows
    easily.

    Parameters
    ----------
    groups : Dict[str, List[str]]
        Pre grouped rows
    runners : int
        Count of runners to group data for should be greater than 0

    Returns
    -------
    List[List[List[str]]]
    """
    grouped_data = [[] for n in range(runners)]
    for index, rows in enumerate(groups.values()):
        grouped_data[index % runners].extend(rows)
    return grouped_data
