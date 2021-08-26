# yamp
## Motivation

You want to document your project. You make an effort and write docstrings. You try Sphinx. You think it sucks and it's slow -- I did. You now want to use ([Material for](https://squidfunk.github.io/mkdocs-material/)) [MkDocs](https://www.mkdocs.org/). You realize it only does rendering and does not parse docstrings. You need some glue in between. This is it.

This is yamp: Yet Another MkDocs Parser. It's opinionated and makes decisions for you. It's what we use to produce the [documentation](https://riverml.xyz/latest/) for [River](https://github.com/online-ml/river/).

## Installation

You should be able to use this with any Python version above or equal to 3.8.

```py
pip install git+https://github.com/MaxHalford/yamp
```

## Usage

Installing `yamp` will give you access to it on the command-line. As an example, assuming you have [River](https://github.com/online-ml/river/) installed, you can do this:

```sh
yamp river --out docs/api
```

This will parse all the modules, classes, and docstrings and dump them in a format that MkDocs understands. Typically, you would run this before calling `mkdocs build`.

Naturally, you can run `yamp -h` to see what options are available.
## Style guide

As a general rule, the docstrings are expected the `numpydoc style guide`. There are just a few extra rules to take into account.

For examples, you may look at [River's source code](https://github.com/online-ml/river/tree/master/river) and check the docstrings therein.

### Parameter typing

Parameter types should not be documented. Instead, they are deduced from the type hints.

**❌ Bad**

```py
class Animal:
    """

    Parameters
    ----------
    name: str
        The animal's name.

    """

    def __init__(self, name):
        self.name = name
```

**✅ Good**

```py
class Animal:
    """

    Parameters
    ----------
    name
        The animal's name.

    """

    def __init__(self, name: str):
        self.name = name
```

### Type hints and docstrings are inherited

If you have a base class with a type hinted method, then you do not have to type hint the method of the child class. The type hints will be inherited. The same goes for docstrings. We found this very useful in River because we have a few base classes that are inherited many times. This saves us from having to copy/paste docstrings all over the place.

**❌ Bad**

```py
import abc

class Animal(abc.ABC):

    @abc.abstractmethod
    def sound(self) -> str:
        """Make some noise.

        Returns
        -------
        The noise.

        """

class Dog(Animal):

    def sound(self) -> str:
        """Make some noise.

        Returns
        -------
        The noise.

        """
        return super().run().upper()
```

**✅ Good**

```py
import abc

class Animal(abc.ABC):

    @abc.abstractmethod
    def sound(self) -> str:
        """Make some noise.

        Returns
        -------
        The noise.

        """

class Dog(Animal):

    def sound(self):
        return super().run().upper()
```

## Alternatives

- [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings)
- [numkdoc](https://github.com/fel-thomas/numkdoc)

## Development

```sh
git clone https://github.com/MaxHalford/yamp
cd yamp

python -m venv .env
source .env/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
python setup.py develop

pytest
```

## License

This project is free and open-source software licensed under the MIT license.
