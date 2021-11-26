import itertools
from typing import (Tuple,
                    Callable,
                    Generator,
                    Union,
                    TypeVar,
                    Iterable,
                    List)
from pathlib import Path
from itertools import chain, islice

"""Source file span"""
Span = Tuple[int, int]

Location = Union[int, Span, None]


class Error():
    """
    An error is a message describing the error together with either
    the line number in which the error occured or a source file span.
    """
    message: str
    location: Location

    def __init__(self, message, location=None):
        self.message = message
        self.location = location

    def brief_summary(self) -> str:
        """
        Return a brief summary of the error in question for logging purposes.
        """
        return f"Error at {self.location}: {self.message}"

    def full_description(self) -> str:
        """
        Returns a full version version of the error in a "nice" form.
        """
        return f"Encountered error at line {self.location}:\n{self.message}"


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
Preprocessor = Callable[[Path], Generator[Tuple[Location, T], None, None]]

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


def flatten_list(list_of_lists):
    return list(chain(*list_of_lists))


def drop(it, n):
    """Drop `n` elements from the front of the iterator `it`
    Adapted from ThiefMaster at https://stackoverflow.com/questions/11113803/pythonic-solution-to-drop-n-values-from-an-iterator
    """
    return islice(it, n, None)
