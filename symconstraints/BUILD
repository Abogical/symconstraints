python_requirements(name="reqs", source="pyproject.toml")

python_sources(name="lib", sources=["symconstraints/*.py"])

resources(name="pyproject", sources=["pyproject.toml"])
files(name="assets", sources=["README.md"])

python_distribution(
    name="dist",
    dependencies=[":pyproject", ":lib", ":assets"],
    provides=python_artifact(name="symconstraints"),
)

python_tests(name="tests", sources=["tests/test_*.py"])
