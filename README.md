# mooc-grader-cont i.e. mgcont

Runs a Docker container for grading an exercise in
[mooc-grader](https://github.com/apluslms/mooc-grader/) style. This stand-alone
project was initiated to accelerate development of automatically assessed
exercises for mooc-grader. This command-line tool supports one-liner testing
and opening shell for debugging inside grading containers.

There are components that could be shared with mooc-grader but currently are
duplicated – it is up to the mooc-grader project to assess if it makes sense to
create dependencies to ensure identical grading execution.


### Installation

Requires [Docker](https://www.docker.com/) installation. The tool is available
from PyPi.

    # pip install mgcont

### Usage

    # mgcont --help
    usage: __main__.py [-h] [--receiver] [--cleanup] [-c CONFIG]
                       [-f FILE [FILE ...]] [-d DIR] [--values VALUES] [--debug]

    Constructs and runs grading containers to test exercises for mooc-grader. Use
    "docker attach mgcont_receiver" to view grading results.

    optional arguments:
      -h, --help            show this help message and exit
      --receiver            only start the receiver
      --cleanup             remove any remaining containers and temporary files
      -c CONFIG, --config CONFIG
                            a mooc-grader exercise configuration yaml/json
      -f FILE [FILE ...], --file FILE [FILE ...]
                            a file to submit
      -d DIR, --dir DIR     a directory including the files to submit
      --values VALUES       a yaml/json file to use as posted values, "meta" can
                            be defined to simulate server provided meta-data
      --debug               run a debug shell instead of the configured grading
                            command

When mgcont is run, the system always creates a receiver-container and
configures it to receive grading results from other mgcont-commands. When
attached to a terminal, the receiver logs every HTTP request until the receiver
is stopped with `ctrl-c`. We recommend to open a second terminal and set it up
to display grading results before testing exercises, e.g.

    # mgcont --receiver
    View with: docker attach mgcont_receiver
    # docker attach mgcont_receiver

Then we can use the first terminal to test exercises and the second to view the
grading results. For example, following submits a single selected file to the
selected exercise for grading. If the exercise is working correctly the result
will appear in the receiver terminal.

    # mgcont -c exercise01/config.yaml -f /path/my_program.py

In contrast to the previous command, following will not run the configured
grading `cmd` inside the container but rather execute a bash shell and attach
to the running container. This allows to e.g. inspect the file system state,
run distinct parts of the designed grading process and inspect their outputs,
and finally run `grade` to see how the collected feedback and results are
delivered to the receiver terminal.

    # mgcont -C exercise01/config.yaml --file /path/my_program.py --debug
    Running debug shell instead of the configured cmd. Attach to it with docker.
      cmd:     /exercise/run.sh
      shell:   docker attach infallible_tharp
    # docker attach infallible_tharp
    root@1b2d5aaccbd3:/submission# ls -al
    total 12
    drwxr-xr-x 2 1496283 70000 4096 Oct 27 11:45 .
    drwxr-xr-x 1 root    root  4096 Oct 27 11:45 ..
    -rw-r--r-- 1 1496283 70000  811 Oct 27 11:45 e01_program.py
    root@1b2d5aaccbd3:/submission# ls /exercise/
    config.yaml  grader_tests.py  tests.py  run.sh	test_config.yaml
    root@1b2d5aaccbd3:/submission# capture echo "Results!"
    root@1b2d5aaccbd3:/submission# capture echo "TotalPoints: 1"
    root@1b2d5aaccbd3:/submission# capture echo "MaxPoints: 2"
    root@1b2d5aaccbd3:/submission# grade
    root@1b2d5aaccbd3:/submission# exit

The following is a convenience command to clean up temporary directories and
any remaining debug containers, receiver container, docker network, and
temporary submission files in the current directory (submission_tmp).

    # mgcont --cleanup

Tip: it is a good idea to include `submission_tmp/` in the `.gitignore` to
avoid accidental commits of temporary files.

### Exercise design (for mooc-grader)

The system has been designed to support automated assessment & feedback – most
typically for various types of programming exercises but the design is not
limiting the exercises to that use only. Along instructional material, the
exercise configuration defines post values and/or files that the student
submits for grading. The exercise furthermore defines a `container -> image`
that is run for the grading. Various images supporting different programming
languages & environments are available under **apluslms** in
[GitHub](https://github.com/orgs/apluslms/repositories) and
[dockerhub](https://hub.docker.com/). The following mounts are made for the
container

* `/submission` = the submitted values and files
* `/exercise` = path configured in `container -> mount`
* other read-only paths configured in `container -> mounts`

The exercise runs the configured `container -> cmd` inside the container. At
the end, the grading must HTTP post the results to `$REC/container-post`. Any
containers that inherit from `apluslms/grading-base` will use a cmd-wrapper
that automatically posts the results at the end, unless grading scripts have
executed `grade` to post them before.

* [Exercise configuration documented at mooc-grader](https://github.com/apluslms/mooc-grader/tree/master/courses)
* [The grading container base](https://github.com/apluslms/grading-base)
