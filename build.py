from setuptools_cpp import ExtensionBuilder, Pybind11Extension

ext_modules = [
    Pybind11Extension("xdma_api",
                      include_dirs=["src"],
                      sources=["src/xdma_api.cpp", "src/xdma_win.cpp"],
                      ),
]


def build(setup_kwargs):
    """
    This function is mandatory in order to build the extensions.
    """
    setup_kwargs.update(
        {"ext_modules": ext_modules, "cmdclass": {"build_ext": ExtensionBuilder}}
    )
