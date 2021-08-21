import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8").read()


setup(
    name="yamp",
    version="0.0.1",
    author="Max Halford",
    license="MIT",
    author_email="maxhalford25@gmail.com",
    description="Yet Another MkDocs Parser",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/MaxHalford/yamp",
    packages=["yamp"],
    python_requires=">=3.8",
    install_requires=["numpydoc"],
    extras_require={
        "dev": ["black", "pytest"],
    },
)
