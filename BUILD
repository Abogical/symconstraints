python_requirements(name="reqs", source="pyproject.toml")

resources(name="pyproject", sources=["pyproject.toml"])
file(name="assets", source="README.md")

python_distribution(
    name="dist",
    dependencies=[":pyproject", "src/symconstraints", ":assets"],
    provides=python_artifact(name="symconstraints"),
)
