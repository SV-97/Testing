import toml
from pathlib import Path
import impl
from base import Preprocessor, ChunkVerifier
from abc import ABC
from dataclasses import dataclass, field
from typing import List, Optional
from itertools import chain


@dataclass
class TestSpec(ABC):
    """A test specification (parsed config file)
    source_path : the path to the input file/folder
    setup : a bash command that's executed before running the test (e.g. make)
    """
    source_path: Optional[Path] = field(init=False, default=None)
    setup: Optional[str] = field(init=False, default=None)


@dataclass
class FileComparison(TestSpec):
    comparison_file: Path
    source_prepro: Preprocessor
    comp_prepro: Preprocessor
    verifier: ChunkVerifier


@dataclass
class ErrorSpec(TestSpec):
    """ Not an actual specification - used to notify the
    user about misformed specifications (e.g. unknown test methods).
    """
    message: str


def parse_file_comparison(parsed_toml: dict):
    params = parsed_toml["parameters"]
    s_prepro = impl.lookup_preprocessor(params['source_preprocessor'])
    c_prepro = impl.lookup_preprocessor(params.get("comparison_preprocessor",
                                                   params['source_preprocessor']))
    verifier = impl.lookup_verifier(params['verifier'])
    return FileComparison(
        Path(params["comparison_file"]),
        lambda path: s_prepro(path, **params.get(
            "source_preprocessor_params", {})),
        lambda path: c_prepro(path, **params.get(
            "comparison_preprocessor_params",
            params.get("source_preprocessor_params", {}))),
        lambda left, right: verifier(left, right, **params.get(
            "verifier_params", {}))
    )


def parse(source: str) -> List[TestSpec]:
    t = toml.loads(source)
    specs = []
    for test_entry in t:
        if type(t[test_entry]) != dict:
            continue
        else:
            parser = globals().get(
                f"parse_{test_entry}",
                None)
            if parser is not None:
                multi_tests = list(filter(str.isdigit, t[test_entry].keys()))
                if len(multi_tests) > 0:
                    new_specs = [parser(t[test_entry][m])
                                 for m in multi_tests]
                else:
                    new_specs = [parser(t[test_entry])]
            else:
                new_specs = [ErrorSpec(
                    f"Invalid specification: unknown test method `{test_entry}`")]
        for spec in new_specs:
            spec.source_path = t["source_path"]
            spec.setup = t.get("setup", None)
        specs.extend(new_specs)
    return specs
