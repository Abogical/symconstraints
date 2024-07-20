python_requirement(
    name="reqs", requirements=["mkdocs-material", "mkdocstrings[python]"]
)

pex_binary(
    name="build",
    dependencies=[":reqs", "//:reqs"],
    script="mkdocs",
    args=["build", "-d", "dist/docs"],
)

pex_binary(
    name="serve",
    dependencies=[":reqs", "//:reqs"],
    script="mkdocs",
    args=["serve"],
)
