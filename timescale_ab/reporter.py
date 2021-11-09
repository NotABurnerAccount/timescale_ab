from statistics import fmean, median
from typing import List


def report(query_times: List[float]) -> str:
    """Generates a report of query time statistics

    Parameters
    ----------
    query_times: List[float]
        Time taken to execute queries

    Returns
    -------
    str
        The formatted report
    """
    return f"""
Queries Performed:      {len(query_times)}
Total Processing Time:  {sum(query_times)}
Minimum Query Time:     {min(query_times)}
Median Query Time:      {median(query_times)}
Average Query Time:     {fmean(query_times)}
Max Query Time:         {max(query_times)}
    """
