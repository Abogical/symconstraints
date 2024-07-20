python_requirement(name="docs-reqs", requirements=["pdoc"])

pdoc_args = ["src/symconstraints", "--math", "--docformat", "numpy"]

pex_binary(
    name="docs-serve",
    dependencies=[":docs-reqs", ":reqs"],
    script="pdoc",
    args=[*pdoc_args, "-n"],
)

pex_binary(
    name="docs-build",
    dependencies=[":docs-reqs", ":reqs"],
    script="pdoc",
    args=[*pdoc_args, "-o", "dist/docs"],
)

python_requirement(name="pytest-reqs", requirements=["pytest", "pytest-cov", "ipdb"])

python_requirements(name="reqs", source="pyproject.toml")

resources(name="pyproject", sources=["pyproject.toml"])
file(name="assets", source="README.md")

python_distribution(
    name="dist",
    dependencies=[":pyproject", "src/symconstraints", ":assets"],
    provides=python_artifact(name="symconstraints"),
)
