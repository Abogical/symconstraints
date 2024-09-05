docs_deps = [f"//:reqs#{dep}" for dep in ["mkdocs-material", "mkdocstrings"]]

pex_binary(
    name="make_logo",
    entry_point="cairosvg",
    dependencies=["//:reqs#cairosvg"],
    args=["docs/logo.svg", "-o", "docs/logo.png"],
)

pex_binary(
    name="build",
    dependencies=docs_deps,
    script="mkdocs",
    args=["build", "-d", "dist/docs"],
)

pex_binary(
    name="serve",
    dependencies=docs_deps,
    script="mkdocs",
    args=["serve"],
)
