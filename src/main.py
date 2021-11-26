from pathlib import Path
from base import Error, flatten_list, FileChecker, Test
from toml_parser import ErrorSpec, parse, FileComparison
from typing import List, Iterable
import logging
from clint.textui import puts, indent, colored, max_width, progress
import click
import os
from time import sleep
import subprocess


def print_with_terminal_width(text):
    terminal_width = os.get_terminal_size().columns
    limit = terminal_width - 10
    if len(text) > limit:
        t = max_width(text, limit)
        lines = t.split("\n")
        puts(lines[0])
        with indent(2):
            puts("\n".join(lines[1:]))
    else:
        puts(text)


def file_comparison(spec: FileComparison) -> List[Error]:
    errors = []
    for ((source_loc, source_val), (_comp_loc, comp_val)) in zip(
            spec.source_prepro(spec.source_file),
            spec.comp_prepro(spec.comparison_file)):
        new_errors = spec.verifier(source_val, comp_val)
        for error in new_errors:
            error.location = source_loc
        errors.extend(new_errors)
    return errors


def folder_comparison(folder: Path, file_comparisons: List[FileChecker]):
    return flatten_list([checker(file) for file, checker in zip(folder, file_comparisons)])


# def test_files(tests: Iterable[Test], logger: Logger) -> bool:
#     """
#     Processes a bunch of tests and logs the results, finally telling us if any errors occured.
#     So a return of `True` means there was some error - and a return of `False` that there were None.
#     """
#     success = True
#     # this loop could be parallelized
#     for (file, verifier) in tests:
#         errors = verifier(file)
#         if len(errors) > 0:
#             success = False
#             for error in errors:
#                 logger.error(f"Error for {file}: {error.brief_summary()}")
#                 print(f"Error for {file}: {error.full_description()}")
#         else:
#             logger.info(f"Success for {file}")
#             print(f"Success for {file}")
#     return success


@click.command()
@click.option("--verbose", "-v",
              type=click.Choice(["0", "1", "2"]),
              default="0", help="Sets verbosity of error reporting.\n"
              " 0: only top-level messages."
              " 1: show a handful of detailed errors."
              " 2: show all errors in full detail.")
@click.option("--files", "-f",
              multiple=True, type=Path,
              default=[
                  "../examples/test_example_1.toml",
                  "../examples/test_example_2.toml",
                  "../examples/test_example_3.toml",
                  "../examples/test_example_4.toml",
                  "../examples/test_example_5.toml",
                  "/home/stefan/GitHub/Testing/examples/microstrip_post_mesh_2.toml"],
              help="Test specification files to run. You may specify multiple files this way, e.g. `-f path1 -f path2 ...`.")
@click.option("--log-file", "-lf", type=Path,
              default="./log.txt", help="Where to save the logfile.")
@click.option("--log-level", "-ll",
              type=click.Choice(list(map(str,
                                         [logging.DEBUG, logging.INFO,
                                          logging.ERROR, logging.CRITICAL]))),
              default=str(logging.INFO), help="What to log.")
def main(files, verbose, log_file, log_level):
    # set up the logger
    handler = logging.FileHandler(filename=log_file, mode="w")
    formatter = logging.Formatter(
        #fmt='{asctime} [{levelname:8}] from {module:>20}.{funcName:30} "{message}"',
        fmt='{asctime} [{levelname:8}]: {message}',
        style="{",
        datefmt="%Y-%m-%dT%H:%m:%S")
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(int(log_level))

    logger.info("Starting run")

    for file in files:
        if not file.exists():
            puts(colored.red(f"File/folder {file.name} does not exist"))
            logger.error(f"File/folder {file.name} does not exist")
            continue

        with file.open() as f:
            specs = parse(f.read())

        for spec in specs:
            # start by running the file's setup command
            if spec.setup is not None:
                try:
                    subprocess.run(spec.setup,
                                   shell=True,
                                   check=True,
                                   capture_output=True,
                                   text=True)
                except subprocess.CalledProcessError as e:
                    message = f"Failed to execute setup for {file.name}: {e}"
                    puts(colored.red(message))
                    if verbose == "2":
                        with indent(4, "|"):
                            puts(colored.red(f"Captured stdout:"))
                            with indent(2):
                                puts(e.stdout)
                            puts(colored.red(f"Captured stderr:"))
                            with indent(2):
                                puts(e.stderr)
                    logger.error(message)
                    continue
            # and proceed by actually executing the specified test
            if type(spec) == FileComparison:  # add more comparison types here
                errors = file_comparison(spec)
            elif type(spec) == ErrorSpec:
                errors = [Error(f"Erronous specification: {spec.message}")]
            else:
                raise NotImplementedError(
                    f"Spec not implemented: {type(spec)}")
            if len(errors) == 0:
                # may want to make the specification checkers (e.g. `file_comparison`) return
                # a `Status` rather than an `Error` to improve diagnostics for multi test files.
                # This would allow us to get more granual output to show where exactly we
                # succeeded.
                puts(colored.green(f"No errors for {file.name}"))
                logger.info(f"No errors for {file}")
            else:
                puts(colored.red(f"Encountered errors for {file.name}"))
                logger.error(f"Encountered errors for {file.name}")
                if verbose != "0":
                    errors_to_print = errors if verbose == "2" else errors[:5]
                    with indent(4, "|"):
                        for error in errors_to_print:  # only print some errors
                            print_with_terminal_width(error.full_description())
                        for error in errors:  # but log all of them
                            logger.debug(
                                f"Error for {file.name}: {error.brief_summary()}")
                        if errors_to_print != errors:
                            print_with_terminal_width(
                                f"... and {len(errors) - len(errors_to_print)} further errors")
        sleep(0.5)
    # print([e.message for e in errors])
    logger.info("Finished run")


if __name__ == "__main__":
    main()  # [Path("../examples/test_example.toml")]
