# Testing
A python library to specify and run automated tests.

## Example output

<pre><font color="#8AE234"><b>user</b></font>:<font color="#729FCF"><b>~/Testing/src</b></font>$ poetry run python ./main.py -v 1
<font color="#4E9A06">✔ No errors for test_successful_file_comparison_relative.toml</font>
<font color="#4E9A06">✔ No errors for test_successful_file_comparison_absolute.toml</font>
<font color="#CC0000">⨯ Failed to execute setup for test_failing_setup.toml: Command &apos;echo test &amp;&amp; exit 1&apos; returned non-zero exit status 1.</font>
<font color="#CC0000">⨯ Encountered errors for test_failing_relative.toml</font>
|   Encountered error at line 0:
|     Comparison failed: expected 0.7011588306897147, got 0.7011588303133641. Relative error of 5.36755155699726e-10 exceeds 1e-12.
|   Encountered error at line 1:
|     Comparison failed: expected 0.27415401860267014, got 0.274154018512178. Relative error of 3.300776485550927e-10 exceeds 1e-12.
|   Encountered error at line 2:
|     Comparison failed: expected 0.1470714904488539, got 0.14707149030804034. Relative error of 9.574497057911537e-10 exceeds 1e-12.
|   Encountered error at line 3:
|     Comparison failed: expected 0.015126937124993921, got 0.015126937118361994. Relative error of 4.3841840493813077e-10 exceeds 1e-12.
|   Encountered error at line 4:
|     Comparison failed: expected 0.42323417267359376, got 0.4232341726050519. Relative error of 1.6194778989206068e-10 exceeds 1e-12.
|   ... and 95 further errors
<font color="#CC0000">⨯ File/folder test_nonexistant_file.toml does not exist</font>
<font color="#4E9A06">✔ No errors for test_microstrip_post_mesh_2.toml</font>
<font color="#4E9A06">✔ No errors for test_microstrip_post_mesh_2.toml</font>

<font color="#CC0000">Results: failed. 4 passed; 3 failed</font>
</pre>


## CLI

<pre><font color="#8AE234"><b>user</b></font>:<font color="#729FCF"><b>~/Testing/src</b></font>$ poetry run python ./main.py --help
Usage: main.py [OPTIONS]

Options:
  -v, --verbose [0|1|2]           Sets verbosity of error reporting. 0: only
                                  top-level messages. 1: show a handful of
                                  detailed errors. 2: show all errors in full
                                  detail.
  -f, --files PATH                Test specification files to run. You may
                                  specify multiple files this way, e.g. `-f
                                  path1 -f path2 ...`.
  -lf, --log-file PATH            Where to save the logfile.
  -ll, --log-level [DEBUG|INFO|ERROR|CRITICAL]
                                  What to log.
  --help                          Show this message and exit.</pre>
## Basics

This library works as follows:

* You provide one or multiple files or folders via the `-f` command line option.
* The library checks those files/paths for *test specs* and runs those
* While doing so it collects errors and other diagnostics and finally presents those

## Conventions for this document

In the following optionality is indicated using square brackets `[]`.
The type `Callable` is used to denote strings containing python code that evaluates to a function.

## Test specs

A test spec is [TOML file](https://toml.io/en/) that determines one or multiple tests. The basic requirement for a test file is only that it has `source_path` key/entry containing the path to the basic object that should be tested. On this `source_path` we then base one or multiple tests that are specified as tables of the form `[{comparison_type}.parameters]` or `[{comparison_type}.{n}.parameters]`, where `comparison_type` specifies the basic comparison mechanism that is used to test the file and `n` is a natural number (or zero).

Please note the [examples](./examples) if the following explanations are unclear.

___

### `comparison_type`

#### `file_comparison`

One possible `comparison_type` are `file_comparison`s where we compare one file with another one. Such a `file_comparison` contains the following `parameter`s:

 | Name         | Description|
|--------------|-----------|
| `comparison_file` | Path to the file we want to compare with |
| `source_preprocessor` | A `preprocessor` that turns the file into comparable elements (*tokens* if you will). |
|`source_preprocessor_params`| Additional parameters for the preprocessor. |
|`verifier`| A way to actually compare two tokens. |
|`verifier_params`| Additional parameters for the verifier. |

___

### `preprocessor`

#### `lines`

Processes the lines of a file one after another.

 | Parameter    |  Type  | Description|
 |---|---|---|
 |[`in_skip`]| `int` | Determines how many lines should be skipped at the beginning of the file. |
 |[`start_pred`]| `Callable` | The preprocessor will call this function with the lines and start actually producing tokens once this predicate is `True`. |
 |[`stop_pred`]| `Callable` | Similarly to `start_pred` the preprocessor will stop producing values once this predicate is `True`. |
 |[`processing_pipeline`]| `List[Callable]` | A sequence of functions that are applied (from left to right) to each token before it is yielded from the preprocessor. This might be used to do any conversions or extract specific values from a line. |

___

### `verifier`

#### `elementwise`
The `elementwise` verifier will take corresponding pairs of tokens from the source and comparison preprocessors and compare them using another set of verifiers.

 | Parameter    |  Type  | Description|
 |---|---|---|
 |`verifiers`| `List[dict]` | List of dictionaries where each entry specifies another `verifier` via its `name` and `args`. |

##### `absolute_error`

Compares two floats via their absolute error.

 | Parameter    |  Type  | Description|
 |---|---|---|
 |`max_error`| `float` | The maximal admissible error allowed to consider two values as equal. |
 
##### `relative_error`

Compares two floats via their relative error.

 | Parameter    |  Type  | Description|
 |---|---|---|
 |`max_error`| `float` | The maximal admissible error allowed to consider two values as equal. |

##### `strict`

Compares two tokens for absolute equality in whatever sense specified by their type.

 | Parameter    |  Type  | Description|
 |---|---|---|
 |---| --- | --- |

___
