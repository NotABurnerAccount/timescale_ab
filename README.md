# Timescale AB/homework assignment

This program is a tool to be used in evaluating the performance of queries against a sample hypertable in timescaledb. Alternately they could be used to evaluate performance on a different hypertable(or non hypertable) if the other table shared the same columns as the sample here. That is if the other table to evaluate query performance has at least the following:

```
(
  ts	TIMESTAMPTZ,
  host	TEXT,
  usage	DOUBLE PRECISION
)
```

Also despite the fact that this tool can work on other tables which have the same columns it will only query from these specific fields as part of the test. It is up to the table and database whether this means other schemas will change performance characteristics.

## How to use

### Required Software

Generally this program is written with the expectation of a linux environment. It may be usable on windows/macOS but hasn't been tested there.
In order to use this software a few other softwares are required, before proceeding please install:

1. python3.8
2. poetry https://python-poetry.org/docs/#installation
3. psql in ubuntu available through `postgresql-client-12` https://www.postgresql.org/download/linux/ubuntu/
4. RECOMMENDED `podman` or `docker` to run timescaledb in a container
5. ALTERNATE TO RECOMMENDATION timescaledb on your host https://docs.timescale.com/timescaledb/latest/how-to-guides/install-timescaledb/self-hosted/
6. OPTIONAL make

You must install all of 1-4 or all of 1-3+5.

### Quickstart

```
$ poetry install
$ poetry run tsab container query_params.csv docker
```

or adjust with your connection options below

```
$ poetry install
$ psql -U postgres < timescale_ab/data/cpu_usage.sql
$ psql -U postgres -d homework -c "\COPY cpu_usage FROM timescale_ab/data/cpu_usage.csv CSV HEADER"
$ poetry run tsab existing query_params.csv --connection-string postgres://user:password@host:port/homework
```

Usage help:
```
usage: tsab container [-h] [--runners RUNNERS] [--cleanup] file_path {docker,podman}
usage: tsab existing [-h] [--runners RUNNERS] [--connection-string CONNECTION_STRING] file_path
```

### Running the software

With the above software installed the most straightforward way to use the software is to run from this repo's root directory:

```sh
$ poetry install
$ poetry run tsab
```

If you've also installed `make` you can make use of it to build a zipapp version of the tool:

```sh
$ make tsab
$ ./tsab
```

Either of these sets of commands will cause the `tsab` tool to display its help message that shows its two subcommands:

```
usage: tsab [-h] {container,existing} ...
tsab: error: the following arguments are required: start_option
```

The remaining sections will assume that you've built the zipapp version of the tool and can run it like `./tsab`; if this does not work in your environment please replace occurences of `./tsab` below with `poetry run tsab`.

#### Running in contianers

If you've elected to install `podman` or `docker` then `tsab` can handle all of the set up for you with:

```
$ ./tsab container <query_param.csv path> <podman|docker>
```

This will cause tsab to bootstrap an instance of timescaledb using the container software of your choice between docker and podman, create the schema in `timescale_ab/cpu_usage.sql`, and copy the data from `timescaledb/cpu_usage.csv` into the `cpu_usage` table. During this process you will see the output of the container software in addition to a check for readiness against the database.

Once the readiness check on the database passes, this tool will run the benchmark against the containerized timescaledb that it bootstrapped and populated. You will see a report like:

```
Queries Performed:      200
Total Processing Time:  0.37534546852111816
Minimum Query Time:     0.0011129379272460938
Median Query Time:      0.0014505386352539062
Average Query Time:     0.0018767273426055907
Max Query Time:         0.010052680969238281
```

The tool will then exit.

After bootstrapping a timescaledb container in this fashion you can continue to use the same container for further benchmarking with the tool like:

```
% ./tsab existing <query_param.csv path>
```

#### Running on your host

If you'd prefer not to use either `podman` or `docker` then please start your timescaledb instance on your host.

After doing this you will need to run the following commands to create the schema  and populate the `cpu_usage` table:

```
$ psql -U postgres < timescale_ab/data/cpu_usage.sql
$ psql psql -U postgres -d homework -c "\COPY cpu_usage FROM timescale_ab/data/cpu_usage.csv CSV HEADER"
```

Note you'll need to adjust the command line options sent psql if you're running on a different host (timescale cloud, aws, etc), with a different user, etc.

Now you're ready to use the `tsab` tool with your timescaledb connection string formated like  `postgres://user:password@host:port/homework`:

```
$ ./tsab existing <query_param.csv path> --connection_string <connection_string>
```

##### Getting help

Both the `container` and `existing` subcommands provide a help message to explain their parameters to access these run the following:

```
$ ./tsab container --help
usage: tsab container [-h] [--runners RUNNERS] [--cleanup] file_path {docker,podman}

positional arguments:
  file_path          Path to file of query params to use for benchmarking
  {docker,podman}    Contianer software to start database with

optional arguments:
  -h, --help         show this help message and exit
  --runners RUNNERS  Number of concurrent runners to use for benchmarks (default 10)
  --cleanup          After running the benchmark remove the running container
$ ./tsab existing --help
usage: tsab existing [-h] [--runners RUNNERS] [--connection-string CONNECTION_STRING] file_path

positional arguments:
  file_path             Path to file of query params to use for benchmarking

optional arguments:
  -h, --help            show this help message and exit
  --runners RUNNERS     Number of concurrent runners to use for benchmarks (default 10)
  --connection-string CONNECTION_STRING
                        Connection string to connect to the existing database (default postgresql://postgres:password@localhost:5432/homework)
```

### Some design decisions

1. This implementation opts to use parallelism rather than strictly concurrency. This seems to make the most sense given the requirement of multiple distict runners. Also it has a (imo) nicer api in python.
2. This implementation opts to run a multiprocess.Pool.map over host grouped data, an alternative approach would have been to use a similar pool of workers but pass each of them a distinct input queue ( so they recieve only query params related to their assigned host(s)) along with a shared output queue and within the main process pull from the shared output queue. This alternative approach would be more straight forward in go with first class channel support ( but is also possible in python ). This alternative approach also has the advantage of not requiring that the entire `query_params.csv` file be in memory at once since lines can be streamed directly to the correct (assigned by host) queue. This alternative approach would also allow the output queue to apply back pressure to the concurrent workers if they were producing too fast since the `output_queue.put` method would block if the queue length exceeded a predecided value; further allowing this alternative approach to limit memory consumption. Given the size of the provided `query_params.csv` performance of the chosen approach should be sufficient and memory consumption should not become an issue.
3. Generally this program implements rather limited error handling, there is very little the program can do to recover from most errors other than silently ignore them; so instead of silently ignoring errors the program does its best to emit Exception messages which describe what the error is. When using a subprocess the program also displays the output of the subprocess providing the error messages of any program used in a subprocess in addition to an Exception message to describe it. A benefit of this approach is that most of it is handled by other libraries, packages, and programs used by this program simplifying the implementation. This is also done with the expectation that the primary users of this application would be technical users and a traceback/exception is a familiar sight. The argumentparser used represents a slight departure from this philosphy since it is very easy to catch wrong cli input (in terms of wrong types). Given more time, more astheticly pleasing error handling could be implemented but in this case I would consider it to add little value.
