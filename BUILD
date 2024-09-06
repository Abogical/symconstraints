python_requirements(name="reqs", source="pyproject.toml")

resources(name="pyproject", sources=["pyproject.toml"])
file(name="assets", source="README.md")

vcs_version(
    name="version",
    generate_to="src/symconstraints/__version__.py",
    local_scheme="no-local-version",
    template='__version__ = "{version}"',
)

python_distribution(
    name="dist",
    dependencies=[":pyproject", "src/symconstraints", ":assets", ":version"],
    provides=python_artifact(name="symconstraints"),
    repositories=["@pypi"],
)
