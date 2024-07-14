python_requirement(name="docs-reqs", requirements=["pdoc"])

pdoc_args = ["symconstraints/symconstraints", "--math"]

pex_binary(
    name="docs-serve",
    dependencies=[":docs-reqs", "symconstraints:reqs"],
    script="pdoc",
    args=[*pdoc_args, "-n"],
)

pex_binary(
    name="docs-build",
    dependencies=[":docs-reqs", "symconstraints:reqs"],
    script="pdoc",
    args=[*pdoc_args, "-o", "dist/docs"],
)
