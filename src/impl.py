from base import Error, drop, ChunkVerifier
from pathlib import Path
from typing import List, Type, TypeVar
from functools import reduce
import re
from itertools import cycle

T = TypeVar("T")


def lookup_verifier(name):
    return globals()[f"{name}_verifier"]


def lookup_preprocessor(name):
    return globals()[f"{name}_preprocessor"]


def relative_error_verifier(calculated: float, reference: float, *, max_error: float):
    error = abs(calculated - reference) / reference
    if error < max_error:
        return []  # no error
    else:
        return [Error(f"Comparison failed: expected {reference}, "
                      f"got {calculated}. Relative error of {error} exceeds {max_error}.")]


def absolute_error_verifier(calculated: float, reference: float, *, max_error: float):
    error = abs(calculated - reference)
    if error < max_error:
        return []  # no error
    else:
        return [Error(f"Comparison failed: expected {reference}, "
                      f"got {calculated}. Absolute error of {error} exceeds {max_error}.")]


def strict_verifier(calculated, reference):
    if calculated == reference:
        return []  # no error
    else:
        return [Error(f"Comparison failed: expected {reference}, "
                      f"got {calculated}.")]


def elementwise_verifier(source_values: List[T], comparison_values: List[T], *, verifiers: List[dict]):
    errors = []
    for s_val, c_val, ver in zip(source_values, comparison_values, cycle(verifiers)):
        errors.extend(lookup_verifier(ver["name"])(
            s_val, c_val, **ver["args"]))
    return errors


def lines_preprocessor(path: Path, *, processing_pipeline: List[str] = [], in_skip=0, start_pred="", stop_pred=""):
    loc = locals()
    # add regular expressions so that they're easily accessible in the pipeline
    loc["re"] = re
    fs = [eval(f, loc) for f in processing_pipeline]
    def f(x): return reduce(lambda acc, f: f(acc), fs, x)
    if start_pred == "":
        def start_pred(_): return True
    else:
        start_pred = eval(start_pred, loc)
    if stop_pred == "":
        def stop_pred(_): return False
    else:
        stop_pred = eval(stop_pred, loc)
    for line_number, line in drop(enumerate(open(path, "r")), in_skip):
        if not start_pred(line):
            continue
        if stop_pred(line):
            break
        yield line_number, f(line)
