# Contributing guide

## Setup

Symbolic Constraints uses the [Pants build system](https://www.pantsbuild.org/) for development. Follow the [Pants installation guide](https://www.pantsbuild.org/stable/docs/getting-started/installing-pants) to set up the development environment.

## Test

Tests are written using [PyTest](https://docs.pytest.org) at `tests/symconstraints`.

Use Pants to run the test suite:

```
pants test ::
```

You can run a specific test if needed. For example the following can be used to only run a specific function in the Pandas test suite:

```
pants test tests/symconstraints/test_pandas.py -- -k test_set_invalid_min
```

### Debug

You can also start a debug adapter to connect to your IDE's debugger with the `--debug-adapter` option:

```
$ pants test --debug-adapter tests/symconstraints/test_pandas.py --no-test-use-coverage -- -k test_set_invalid_min
23:43:22.24 [INFO] Launching debug adapter at '127.0.0.1:5678', which will wait for a client connection...
```

[See this documentation](https://www.pantsbuild.org/stable/docs/python/goals/test) of `pants test` for more details.

## Type checking

Symbolic Constraints makes heavy use of [Python typing](https://docs.python.org/3/library/typing.html). Static type checking can be done within Pants via the following command:

```
pants check ::
```

## Documentation

A live server of the documentation can be run via:

```
pants run docs:serve
```

## Formatting and Linting

Make sure to format and lint your code before submitting your contribution.

### Format
```
pants fmt ::
```

### Lint
```
pants lint ::
```

