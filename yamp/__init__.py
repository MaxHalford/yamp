"""This script is responsible for building the API reference. The API reference is located in
docs/api. The script scans through all the modules, classes, and functions. It processes
the __doc__ of each object and formats it so that MkDocs can process it in turn.

"""
import functools
import importlib
import inspect
import os
import pathlib
import re
import shutil

from numpydoc.docscrape import ClassDoc, FunctionDoc

from yamp import md
from yamp import utils


class Linkifier:
    def __init__(self):

        path_index = {}
        name_index = {}

        modules = dict(
            inspect.getmembers(importlib.import_module("river"), inspect.ismodule)
        )
        modules = {
            "base": modules["base"],
            "linear_model": modules["linear_model"],
            "stream": modules["stream"],
            "optim": modules["optim"],
        }

        def index_module(mod_name, mod, path):
            path = os.path.join(path, mod_name)
            dotted_path = path.replace("/", ".")

            for func_name, func in inspect.getmembers(mod, inspect.isfunction):
                for e in (
                    f"{mod_name}.{func_name}",
                    f"{dotted_path}.{func_name}",
                    f"{func.__module__}.{func_name}",
                ):
                    path_index[e] = os.path.join(path, utils.snake_to_kebab(func_name))
                    name_index[e] = f"{dotted_path}.{func_name}"

            for klass_name, klass in inspect.getmembers(mod, inspect.isclass):
                for e in (
                    f"{mod_name}.{klass_name}",
                    f"{dotted_path}.{klass_name}",
                    f"{klass.__module__}.{klass_name}",
                ):
                    path_index[e] = os.path.join(path, klass_name)
                    name_index[e] = f"{dotted_path}.{klass_name}"

            for submod_name, submod in inspect.getmembers(mod, inspect.ismodule):
                if submod_name not in mod.__all__ or submod_name == "typing":
                    continue
                for e in (f"{mod_name}.{submod_name}", f"{dotted_path}.{submod_name}"):
                    path_index[e] = os.path.join(
                        path, utils.snake_to_kebab(submod_name)
                    )

                # Recurse
                index_module(submod_name, submod, path=path)

        for mod_name, mod in modules.items():
            index_module(mod_name, mod, path="")

        # Prepend river to each index entry
        for k in list(path_index.keys()):
            path_index[f"river.{k}"] = path_index[k]
        for k in list(name_index.keys()):
            name_index[f"river.{k}"] = name_index[k]

        self.path_index = path_index
        self.name_index = name_index

    def linkify(self, text, use_fences, depth):
        path = self.path_index.get(text)
        name = self.name_index.get(text)
        if path and name:
            backwards = "../" * (depth + 1)
            if use_fences:
                return f"[`{name}`]({backwards}{path})"
            return f"[{name}]({backwards}{path})"
        return None

    def linkify_fences(self, text, depth):
        between_fences = re.compile(r"`[\w\.]+\.\w+`")
        return between_fences.sub(
            lambda x: self.linkify(x.group().strip("`"), True, depth) or x.group(), text
        )

    def linkify_dotted(self, text, depth):
        dotted = re.compile(r"\w+\.[\.\w]+")
        return dotted.sub(
            lambda x: self.linkify(x.group(), False, depth) or x.group(), text
        )


def concat_lines(lines):
    return inspect.cleandoc(" ".join("\n\n" if line == "" else line for line in lines))


def print_docstring(obj, file, depth, linkifier):
    """Prints a classes's docstring to a file."""

    doc = ClassDoc(obj) if inspect.isclass(obj) else FunctionDoc(obj)

    printf = functools.partial(print, file=file)

    printf(md.h1(obj.__name__))
    printf(linkifier.linkify_fences(md.line(concat_lines(doc["Summary"])), depth))
    printf(
        linkifier.linkify_fences(md.line(concat_lines(doc["Extended Summary"])), depth)
    )

    # We infer the type annotations from the signatures, and therefore rely on the signature
    # instead of the docstring for documenting parameters
    try:
        signature = inspect.signature(obj)
    except ValueError:
        signature = (
            inspect.Signature()
        )  # TODO: this is necessary for Cython classes, but it's not correct
    params_desc = {param.name: " ".join(param.desc) for param in doc["Parameters"]}

    # Parameters
    if signature.parameters:
        printf(md.h2("Parameters"))
    for param in signature.parameters.values():
        # Name
        printf(f"- **{param.name}**", end="")
        # Type annotation
        if param.annotation is not param.empty:
            anno = inspect.formatannotation(param.annotation)
            anno = linkifier.linkify_dotted(anno, depth)
            printf(f" (*{anno}*)", end="")
        # Default value
        if param.default is not param.empty:
            printf(f" – defaults to `{param.default}`", end="")
        printf("\n", file=file)
        # Description
        desc = params_desc[param.name]
        if desc:
            printf(f"    {desc}\n")
    printf("")

    # Attributes
    if doc["Attributes"]:
        printf(md.h2("Attributes"))
    for attr in doc["Attributes"]:
        # Name
        printf(f"- **{attr.name}**", end="")
        # Type annotation
        if attr.type:
            printf(f" (*{attr.type}*)", end="")
        printf("\n", file=file)
        # Description
        desc = " ".join(attr.desc)
        if desc:
            printf(f"    {desc}\n")
    printf("")

    # Examples
    if doc["Examples"]:
        printf(md.h2("Examples"))

        in_code = False
        after_space = False

        for line in inspect.cleandoc("\n".join(doc["Examples"])).splitlines():

            if (
                in_code
                and after_space
                and line
                and not line.startswith(">>>")
                and not line.startswith("...")
            ):
                printf("```\n")
                in_code = False
                after_space = False

            if not in_code and line.startswith(">>>"):
                printf("```python")
                in_code = True

            after_space = False
            if not line:
                after_space = True

            printf(line)

        if in_code:
            printf("```")
    printf("")

    # Methods
    if inspect.isclass(obj) and doc["Methods"]:
        printf(md.h2("Methods"))
        printf_indent = lambda x, **kwargs: printf(f"    {x}", **kwargs)

        for meth in doc["Methods"]:

            printf(md.line(f'???- note "{meth.name}"'))

            # Parse method docstring
            docstring = utils.find_method_docstring(c=obj, meth=meth.name)
            if not docstring:
                continue
            meth_doc = FunctionDoc(func=None, doc=docstring)

            printf_indent(md.line(" ".join(meth_doc["Summary"])))
            if meth_doc["Extended Summary"]:
                printf_indent(md.line(" ".join(meth_doc["Extended Summary"])))

            # We infer the type annotations from the signatures, and therefore rely on the signature
            # instead of the docstring for documenting parameters
            signature = utils.find_method_signature(obj, meth.name)
            params_desc = {
                param.name: " ".join(param.desc) for param in doc["Parameters"]
            }

            # Parameters
            if (
                len(signature.parameters) > 1
            ):  # signature is never empty, but self doesn't count
                printf_indent("**Parameters**\n")
            for param in signature.parameters.values():
                if param.name == "self":
                    continue
                # Name
                printf_indent(f"- **{param.name}**", end="")
                # Type annotation
                if param.annotation is not param.empty:
                    printf_indent(
                        f" (*{inspect.formatannotation(param.annotation)}*)", end=""
                    )
                # Default value
                if param.default is not param.empty:
                    printf_indent(f" – defaults to `{param.default}`", end="")
                printf_indent("", file=file)
                # Description
                desc = params_desc.get(param.name)
                if desc:
                    printf_indent(f"    {desc}")
            printf_indent("")

            # Returns
            if meth_doc["Returns"]:
                printf_indent("**Returns**\n")
                return_val = meth_doc["Returns"][0]
                if signature.return_annotation is not inspect._empty:
                    if inspect.isclass(signature.return_annotation):
                        printf_indent(
                            f"*{signature.return_annotation.__name__}*: ", end=""
                        )
                    else:
                        printf_indent(f"*{signature.return_annotation}*: ", end="")
                printf_indent(return_val.type)
                printf_indent("")

    # Notes
    if doc["Notes"]:
        printf(md.h2("Notes"))
        printf(md.line("\n".join(doc["Notes"])))

    # References
    if doc["References"]:
        printf(md.h2("References"))
        printf(md.line("\n".join(doc["References"])))


def print_module(mod, path, overview, linkifier, is_submodule=False):

    mod_name = mod.__name__.split(".")[-1]

    # Create a directory for the module
    mod_slug = utils.snake_to_kebab(mod_name)
    mod_path = path.joinpath(mod_slug)
    mod_short_path = str(mod_path).replace("docs/api/", "")
    os.makedirs(mod_path, exist_ok=True)
    with open(mod_path.joinpath(".pages"), "w") as f:
        f.write(f"title: {mod_name}")

    # Add the module to the overview
    if is_submodule:
        print(md.h3(mod_name), file=overview)
    else:
        print(md.h2(mod_name), file=overview)
    if mod.__doc__:
        print(md.line(mod.__doc__), file=overview)

    # Extract all public classes and functions
    ispublic = lambda x: x.__name__ in mod.__all__ and not x.__name__.startswith("_")
    classes = inspect.getmembers(mod, lambda x: inspect.isclass(x) and ispublic(x))
    funcs = inspect.getmembers(mod, lambda x: inspect.isfunction(x) and ispublic(x))

    # Classes

    if classes and funcs:
        print("\n**Classes**\n", file=overview)

    for _, c in classes:
        print(f"{mod_name}.{c.__name__}")

        # Add the class to the overview
        slug = utils.snake_to_kebab(c.__name__)
        print(
            md.li(md.link(c.__name__, f"../{mod_short_path}/{slug}")),
            end="",
            file=overview,
        )

        # Write down the class' docstring
        with open(mod_path.joinpath(slug).with_suffix(".md"), "w") as file:
            print_docstring(
                obj=c,
                file=file,
                linkifier=linkifier,
                depth=mod_short_path.count("/") + 1,
            )

    # Functions

    if classes and funcs:
        print("\n**Functions**\n", file=overview)

    for _, f in funcs:
        print(f"{mod_name}.{f.__name__}")

        # Add the function to the overview
        slug = utils.snake_to_kebab(f.__name__)
        print(
            md.li(md.link(f.__name__, f"../{mod_short_path}/{slug}")),
            end="",
            file=overview,
        )

        # Write down the function' docstring
        with open(mod_path.joinpath(slug).with_suffix(".md"), "w") as file:
            print_docstring(
                obj=f,
                file=file,
                linkifier=linkifier,
                depth=mod_short_path.count(".") + 1,
            )

    # Sub-modules
    for name, submod in inspect.getmembers(mod, inspect.ismodule):
        # We only want to go through the public submodules, such as optim.schedulers
        if (
            name in ("tags", "typing", "inspect", "skmultiflow_utils")
            or name not in mod.__all__
            or name.startswith("_")
        ):
            continue
        print_module(
            mod=submod,
            path=mod_path,
            overview=overview,
            linkifier=linkifier,
            is_submodule=True,
        )

    print("", file=overview)


def print_library(library: str, output_dir: pathlib.Path):

    # Create a directory for the API reference
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_dir.joinpath(".pages"), "w") as f:
        f.write("title: API reference\narrange:\n  - overview.md\n  - ...\n")

    overview = open(output_dir.joinpath("overview.md"), "w")
    print(md.h1("Overview"), file=overview)

    linkifier = Linkifier()

    for mod_name, mod in inspect.getmembers(
        importlib.import_module("river"), inspect.ismodule
    ):
        if mod_name.startswith("_"):
            continue
        print(mod_name)
        print_module(mod, path=output_dir, overview=overview, linkifier=linkifier)
