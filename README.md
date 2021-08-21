# yamp
## Motivation

You want to document your project. You make an effort and write docstrings. You try Sphinx. You think it sucks and it's slow -- I did. You now want to use ([Material for](https://squidfunk.github.io/mkdocs-material/)) [MkDocs](https://www.mkdocs.org/). You realize it only does rendering and does not parse docstrings. You need some glue in between. This is it.

This is yamp: Yet Another MkDocs Parser. It's opinionated and makes decisions for you. It's what we use to produce the [documentation](https://riverml.xyz/latest/) for [River](https://github.com/online-ml/river/).

## Installation

You should be able to use this with any Python version above or equal to 3.8.

```py
pip install git+https://github.com/MaxHalford/yamp
```

This gives you access to `yamp` on the command-line. As an example, assuming you have [River](https://github.com/online-ml/river/) installed, you can do this:

```sh
yamp river --out docs/api
```

This will parse all the modules, classes, and docstrings and dump them in a format that MkDocs understands.

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
