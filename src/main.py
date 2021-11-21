from typing import (Tuple,
                    Callable,
                    Generator,
                    Union,
                    TypeVar,
                    Iterable,
                    List)
from pathlib import Path
from logging import Logger

"""Source file span"""
Span = Tuple[int, int]


class Error():
    """
    An error is a message describing the error together with either
    the line number in which the error occured or a source file span.
    """
    message: str
    location: Union[int, Span]

    def brief_summary(self) -> str:
        """
        Return a brief summary of the error in question for logging purposes.
        """

    def full_description(self) -> str:
        """
        Returns a full version version of the error in a "nice" form.
        """


"""
We verify a file by somehow mapping its path
to either `Ok` or an Error with some error message.
So we for example have:
```
def compare_files(path: Path, *, comparison_file : Path) -> List[Error]: pass

comparison_file = ... 
```
which verifies a file by comparing it with another one in some way. In this case the function
`lambda path: compare_files(path, comparison_file)` is a `FileChecker`.
This will either return no errors if everything was succeful or a list of Errors like 
`"Mismatch on line 42: expected value is 123, got 124."` on failure.
"""
FileChecker = Callable[[Path], List[Error]]

T = TypeVar("T")

"""
To process some file we might want some sort of preprocessing (e.g. getting rid of the first
line which might contain column names etc.). This means we take a file and somehow generate
some output values from it (e.g. take all lines and extract a specific value) - we basically
chunk the input file up into some processing units.
"""
Preprocessor = Callable[[Path], Generator[T, None, None]]

"""
We verify all the chunks produced by the preprocessor, producing a (potentially empty) list
of errors along the way.
One example would be:
    * a preprocessor producing tuples of numbers (the numbers from corresponding lines of two files)
    * a chunk verifier that tests whether the relative error of the numbers in that tuple does not
        exceed some threshold.
"""
ChunkVerifier = Callable[[T], List[Error]]


def verify_file(
        file: Path,
        chunker: Preprocessor[T],
        verifier: ChunkVerifier[T],
) -> List[Error]:
    """
    One possibility to test a file is to chunk it up and verify each chunk in some way.
    This means that for each chunker and verifier the function
    ```
    lambda file: verify_file(file, chunker, verifier)
    ```
    will be a `FileChecker`.
    """
    errors = []
    for chunk in chunker(file):
        if len(result := verifier(chunk)) > 0:
            errors.extend(result)
    return errors


"""
A `Test` now is some file (or folder) together with a function telling us how to test the file (or folder).
"""
Test = Tuple[Path, FileChecker]


def test_files(tests: Iterable[Test], logger: Logger) -> bool:
    """
    Processes a bunch of tests and logs the results, finally telling us if any errors occured.
    So a return of `True` means there was some error - and a return of `False` that there were None.
    """
    success = True
    # this loop could be parallelized
    for (file, verifier) in tests:
        if len(errors := verifier(file)) > 0:
            success = False
            for error in errors:
                logger.error(f"Error for {file}: {error.brief_summary()}")
                print(f"Error for {file}: {error.full_description()}")
        else:
            logger.info(f"Success for {file}")
            print(f"Success for {file}")
    return success
