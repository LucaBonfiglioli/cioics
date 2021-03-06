# Choixe - Configurations With Superpowers!

## Introduction

**Choixe** is a mini-language built on top of python that adds some cool features to markup configuration files, with the intent of increasing code reusability and automatizing some aspects of writing configuration files.

- **Variables**: placeholders for something that will be defined later.
- **Imports**: append the content of another configuration file anywhere.
- **Sweeps**: exhaustive search over a parameter space.
- **Python Instances**: calling of dynamically imported python functions.
- **Loops**: foreach-like control that iterates over a collection of elements.

Currently supported formats include: 
- YAML
- JSON

Note that any markup format that can be deserialized into python built-ins can work with **Choixe** syntax. In fact, you can use these features even with no configuration file at all, by just putting some **directives** into a plain python dictionary or list, **Choixe** does not care.

All that **Choixe** does is the following:

```mermaid
flowchart LR
A[File]
B[Python\nStructure]
C[Parsed\nChoixe AST]
D[Python\nStructure]
E[File]
A -.->|Loading| B
B -->|Parsing| C
C -->|Processing| D
D -.->|Writing| E
```

1. Optionally **load** a **structure** from a markup file. The structure usually consists of
   nested python **dictionaries** or **lists**, containing built-in types like integers,
   floats, booleans, strings. 
2. **Parse** the structure into an **AST**, looking for a special syntactic pattern - 
   called **"directive"** - in every string that is found. 
3. **Process** the **AST** by visiting it recursively, resulting in a another python
   structure.
4. Optionally **write** the new structure to a markup file.

For simplicity, in the rest of this tutorial most examples will be written in YAML, as it is less verbose than JSON or python syntax.

## Syntax

As I may have anticipated, **Choixe** features are enabled when a **directive** is found. **Directives** are special strings or special dictionaries that can appear in different forms:
- "compact"
- "call"
- "extended"
- "special"

**Note**: some directives are available only in a subset of the previous forms.

### Compact Form

```yaml
$DIRECTIVE_NAME
``` 

Basically a `$` followed by a name. The name must follow the rules of python identifiers, so only alphanumeric characters and underscores ( `_` ), the name cannot start with a digit.

Examples:
-  `$index`
-  `$item`

Only directives without parameters can be expressed in the compact form.

### Call Form

```yaml
$DIRECTIVE_NAME(ARGS, KWARGS)
```

The call form extends the compact form with a pair of parenthesis containing the directive arguments. Arguments follow the rules of a plain python function call, in fact, they are parsed using the python interpreter.

Examples:
- `$var(x, default=hello, env=False)`
- `$for(object.list, x)`

The compact form is essentially a shortcut for the call form when no arguments are needed: `$model` is equivalent to `$model()`.

**Note**: due to some limitations of the current lexer, call forms can contain **at most** one set of parenthesis, meaning that you are **not** allowed to nest them like this:

- ~~`$directive(arg1=(1, 2, 3))`~~
- ~~`$directive(arg1="meow", arg2=$directive2(10, 20))`~~

If you really need to nest **directives**, you must use the **extended form**, introduced in the next paragraph.

### Extended Form

```yaml
$directive: DIRECTIVE_NAME
$args: LIST_OF_ARGS
$kwargs: DICT_OF_KWARGS
```

The extended form is a more verbose and more explicit alternative that allows to pass complex arguments that cannot be expressed with the current limitations of the call form. 

Examples:
- ```yaml
  $directive: var
  $args:
    - x
  $kwargs:
    default: hello
    env: false
  ```
- ```yaml
  $directive: sweep
  $args:
    - 10
    - [10, 20]
    - a: $var(x, default=30) # Directive nesting
      b: 60
  $kwargs: {}
  ```

### Special Form

Some **directives** are available only with special forms, i.e. some forms that do not have a schema, and depend from the specific **directive** used. Do not worry, they are just a few, they are detailed below and their schema is easy to remember.

### String Bundles

**Directives** can also be mixed with plain strings, creating a "String Bundle":

`$var(animal.name) is a $var(animal.species) and their owner is $var(animal.owner, default="unknown")`

In this case, the string is tokenized into 5 parts:
1. `$var(animal.name)`
2. ` is a `
3. `$var(animal.species)`
4. ` and their owner is `
5. `$var(animal.owner, default="unknown")`

The result of the computation is the string concatenation of the result of each individual token: `Oliver is a cat and their owner is Alice`.

### Directive table

| Directive | Compact | Call  | Extended | Special |
| :-------: | :-----: | :---: | :------: | :-----: |
|   `var`   |    ???    |   ??????   |    ??????     |    ???    |
| `import`  |    ???    |   ??????   |    ??????     |    ???    |
|  `sweep`  |    ???    |   ??????   |    ??????     |    ???    |
|  `call`   |    ???    |   ???   |    ???     |    ??????    |
|  `model`  |    ???    |   ???   |    ???     |    ??????    |
|   `for`   |    ???    |   ???   |    ???     |    ??????    |
|  `item`   |    ??????    |   ??????   |    ??????     |    ???    |
|  `index`  |    ??????    |   ??????   |    ??????     |    ???    |

## Variables

Suppose you have a very long and complex configuration file, and you often need to change some values in it, depending on external factors. You can:

- Manually edit it each time, waste some time looking for the specific value to edit, keep a history of the changes or otherwise you won't be able to go back.
- Keep the files immutable but instead create a duplicate for every possible value, and when you eventually realize something was wrong with the original file, you have to propagate the changes in all the 20.000 copies you created.
- Replace the values you need to change with **Variables**, and let **Choixe** fill in the values for you, keeping only **one**, **immutable** version of the original file.

The following example consists in a toy configuration file for a deep learning training task, involving a moderate amount of parameters. Your configuration file looks like this:

```yaml
model:
  architecture:
    backbone: resnet18
    use_batch_norm: false
    heads:
      - type: classification
        num_classes: 10
      - type: classification
        num_classes: 7
training:
  device: cuda
  epochs: 100
  optimizer: 
    type: Adam
    params:
      learning_rate: 0.001
      betas: [0.9, 0.99]
```

In this toy configuration file there are some parameters entirely dependant from the 
task at hand. Take for instance the number of classes, whenever you decide to perform
a training on a different dataset, the number of classes is inevitably going to change.

To avoid the pitfalls described earlier, you can use **variables**. Think of a **variable** 
as a placeholder for something that will be defined later. **Variables** values are picked at runtime from a structure referred to as **"context"**, that can be passed to **Choixe** python
API.

To use variables, simply replace a literal value with a `var` directive: 

`$var(identifier: str, default: Optional[Any] = None, env: bool = False)`

Where:
- `identifier` is the [pydash](https://pydash.readthedocs.io/en/latest/) path (dot notation only) where the value is looked up in the **context**.
- `default` is a value to use when the context lookup fails - essentially making the variable entirely optional. Defaults to `None`.
- `env` is a bool that, if set to `True`, will also look at the system environment variables in case the **context** lookup fails. Defaults to `False`.

Here is what the deep learning toy configuration looks like after replacing some values with **variables**: 

```yaml
model:
  architecture:
    backbone: resnet18
    use_batch_norm: $var(hparams.normalize, default=True)
    heads:
      - type: classification
        num_classes: $var(data.num_classes1) # No default: entirely task dependant
      - type: classification
        num_classes: $var(data.num_classes2) # No default: entirely task dependant
training:
  device: $var(TRAINING_DEVICE, default=cpu, env=True) # Choose device based on env vars.
  epochs: $var(hparams.num_epochs, default=100)
  optimizer: 
    type: Adam
    params:
      learning_rate: $var(hparams.lr, default=0.001)
      betas: [0.9, 0.99]
```

The minimal **context** needed to use this configuration will look something like this:

```yaml
data:
  num_classes1: 10
  num_classes2: 7
```

The full context can contain all of these options:

```yaml
data:
  num_classes1: 10
  num_classes2: 7
hparams:
  normalize: true # Optional
  num_epochs: 100 # Optional
  lr: 0.001 # Optional
TRAINING_DEVICE: cuda # Optional, env
```

**Contexts** can also be seen as a "meta-configuration" providing an easier and cleaner access to a subset of "public" parameters of a templatized "private" configuration file with lots of details to keep hidden.

## Imports

Imagine having a configuration file in which some parts could be reused in other configuration files. It's not the best idea to duplicate them, instead, you can move those parts in a separate configuration file and dynamically import it using the `import` **directive**.

To use an import directive, replace any node of the configuration with the following directive:

`$import(path: str)`

Where:
  - `path` can be an absolute or relative path to another configuration file. If the path is relative, it will be resolved relatively from the parent folder of the importing configuration file, or, in case there is no importing file, the system current working directive.

Let's build on top of the previous "deep learning" example:

```yaml
model:
  architecture:
    backbone: resnet18
    use_batch_norm: $var(hparams.normalize, default=True)
    heads:
      - type: classification
        num_classes: $var(data.num_classes1)
      - type: classification
        num_classes: $var(data.num_classes2)
training:
  device: $var(TRAINING_DEVICE, default=cpu, env=True)
  epochs: $var(hparams.num_epochs, default=100)
  optimizer: 
    type: Adam
    params:
      learning_rate: $var(hparams.lr, default=0.001)
      betas: [0.9, 0.99]
```

Here, one could choose to factor out the `optimizer` node and move it into a separate file called "adam.yml".

```yaml
# neural_network.yml
model:
  architecture:
    backbone: resnet18
    use_batch_norm: $var(hparams.normalize, default=True)
    heads:
      - type: classification
        num_classes: $var(data.num_classes1)
      - type: classification
        num_classes: $var(data.num_classes2)
training:
  device: $var(TRAINING_DEVICE, default=cpu, env=True)
  epochs: $var(hparams.num_epochs, default=100)
  optimizer: $import(adam.yml)
```

```yaml
# adam.yml
type: Adam
params:
  learning_rate: $var(hparams.lr, default=0.001)
  betas: [0.9, 0.99]
```

Note that "adam.yml" contains some **directives**. This is not a problem and it is handled automatically by **Choixe**. There is also no restriction on using **imports** in imported files, you can nest them as you please.

## Sweeps

**Sweeps** allow to perform an exhaustive search over a parametrization space, in a grid-like fashion, without having to manually duplicate the configuration file.

To use a `sweep` **directive**, replace any node of the configuration with the following **directive**:

`$sweep(*args: Any)`

Where:
- `args` is an arbitrary set of parameters.
  
All the **directives** introduced so far are "non-branching", i.e. they only have one possible outcome. **Sweeps** instead, are currently the only "branching" **Choixe directives**, as they produce multiple configurations as their output.

Example:

```yaml
foo:
  alpha: $sweep(a, b) # Sweep 1
  beta: $sweep(10, 20, hello) # Sweep 2
```

Will produce the following **six** outputs, the cartesian product of `{a, b}` and `{10, 20, hello}`:

1. ```yaml
   foo:
     alpha: a
     beta: 10
   ```
2. ```yaml
   foo:
     alpha: b
     beta: 10
   ```
1. ```yaml
   foo:
     alpha: a
     beta: 20
   ```
2. ```yaml
   foo:
     alpha: b
     beta: 20
   ```
3. ```yaml
   foo:
     alpha: a
     beta: hello
   ```
4. ```yaml
   foo:
     alpha: b
     beta: hello
   ```

```mermaid
flowchart TD
root -->|Sweep 1| a
root -->|Sweep 1| b
a -->|Sweep 2| id1[10]
a -->|Sweep 2| id2[20]
a -->|Sweep 2| id3[hello]
b -->|Sweep 2| id4[10]
b -->|Sweep 2| id5[20]
b -->|Sweep 2| id6[hello]
```

By default, all **sweeps** are global, each of them adds a new axis to the parameter space, regardless of the depth at which they appear in the structure. There is only one exception to this rule: if a **sweep** appears inside a branch of another sweep; in this case, the new axis is added locally.

Example:

```yaml
foo: 
  $directive: sweep # Sweep 1 (global)
  $args:
    - alpha: $sweep(foo, bar) # Sweep 2 (local)
      beta: 10
    - gamma: hello 
  $kwargs: {}
```

Will produce the following **three** outputs:

1. ```yaml
   foo:
     alpha: foo
     beta: 10
   ```
2. ```yaml
   foo:
     alpha: bar
     beta: 10
   ```
3. ```yaml
   foo:
     gamma: hello
   ```

```mermaid
flowchart TD
root -->|Sweep 1| a["{alpha: $sweep(foo, bar), beta: 10}"]
root -->|Sweep 1| b["gamma: hello"]
a -->|Sweep 2| foo
a -->|Sweep 2| bar
```

## Instances
**Instances** allow to dynamically replace configuration nodes with real **python objects**. This can happen in two ways:
- With the `call` **directive** - dynamically import a python function, invoke it and replace the node content with the function result.
- With the `model` **directive** - dynamically import a [pydantic](https://pydantic-docs.helpmanual.io/) `BaseModel` and use it to deserialize the content of the current node.

**Note**: these **directives** can only be used with the **special form**.

### Call 

To invoke a python `Callable`, use the following directive.

```yaml
$call: SYMBOL [str]
$args: ARGUMENTS [dict]
```

Where:
- `SYMBOL` is a string containing either:
  - A filesystem path to a .py file, followed by `:` and the name of a callable.
  - A python module path followed by `.` and the name of a callable.
- `ARGUMENTS` is a dictionary containing the arguments to pass to the callable.

Example:

```yaml
foo: 
  $call: path/to/my_file.py:MyClass
  $args:
    a: 10
    b: 20
```

Will import `MyClass` from `path/to/my_file.py` and produce the dictionary:

```python
{"foo": SomeClass(a=10, b=20)}
```

Another example:

```yaml
foo:
  $call: numpy.zeros
  $args:
    shape: [2, 3]
```

Will import `numpy.zeros` and produce the dictionary:

```python
{"foo": numpy.zeros(shape=[2, 3])}
```

### Model

Similar to `call`, the `model` **directive** will provide an easier interface to deserialize **pydantic** models. 

The syntax is essentially the same as `call`:

```yaml
$model: SYMBOL [str]
$args: ARGUMENTS [dict]
```

In this case, there is the constraint that the imported class must be a `BaseModel` subtype.

## Loops

You want to repeat a configuration node, iterating over a list of values? You can do this with the `for` **directive**, available only with the following **special form**:

```yaml
$for(ITERABLE[, ID]): BODY
```

Where:
- `ITERABLE` is a context key (just like a `var`) that points to a list. The for loop will iterate over the items of this list.
- `ID` is an optional identifier for this for-loop, used to distinguish this specific loop from all the others, in case multiple loops are nested. Think of it like the `x` in `for x in my_list:`. When not specified, **Choixe** will use a random uuid behind the scenes.
- `BODY` can be either:
  - A **dictionary** - the for loop will perform dictionary union over all the iterations.
  - A **list** - the for loop will perform list concatenation over all the iterations.
  - A **string** - the for loop will perform string concatenation over all the iterations.

For-loops alone are not that powerful, but they are meant to be used along two other **directives**:

- `$index(identifier: Optional[str] = None)` or `$index` 
- `$item(identifier: Optional[str] = None)` or `$item`

They, respectively, return the integer index and the item of the current loop iteration. If no identifier is specified (you can use the **compact form**), they will refer to the first for loop encountered in the stack. Otherwise, they will refer to the loop whose identifier matches the one specified. 

Optionally, the `item` **directive** can contain a [pydash](https://pydash.readthedocs.io/en/latest/) key starting with the loop id, to refer to a specific item inside the structure.

Example:
```yaml
alice:
    # For loop that merges the resulting dictionaries
    "$for(params.cats, x)":
        cat_$index(x):
            index: I am cat number $index
            name: My name is $item(x.name)
            age: My age is $item(x.age)
bob:
    # For loop that extends the resulting list
    "$for(params.cats, x)":
        - I am cat number $index
        - My name is $item(x.name)
charlie:
    # For loop that concatenates the resulting strings
    "$for(params.cats, x)": "Cat_$index(x)=$item(x.age) "
``` 
Given the context:
```yaml
params:
  cats:
    - name: Luna
      age: 5
    - name: Milo 
      age: 6
    - name: Oliver
      age: 14
```
Will result in:
```yaml
alice:
  cat_0:
    age: My age is 5
    index: I am cat number 0
    name: My name is Luna
  cat_1:
    age: My age is 6
    index: I am cat number 1
    name: My name is Milo
  cat_2:
    age: My age is 14
    index: I am cat number 2
    name: My name is Oliver
bob:
  - I am cat number 0
  - My name is Luna
  - I am cat number 1
  - My name is Milo
  - I am cat number 2
  - My name is Oliver
charlie: "Cat_0=5 Cat_1=6 Cat_2=14 "
```

## XConfig

All **Choixe** functionalities can be accessed with the `XConfig` class. You can construct an `XConfig` from any python mapping, by simply passing it to the constructor:

```python
from choixe import XConfig

# A dictionary containing stuff
data = {
    "alpha": {
        "a": 10,
        "b": -2,
    },
    "beta": {
        "a": "hello",
        "b": "world",
    },
} 

# Instance an XConfig
cfg = XConfig(data)
```

### Interaction

An `XConfig` is also a python `Mapping` and has all the methods you would expect from a plain python `dict`. 

In addition, you can get/set its contents with the dot notation (if you know the keys at code time) like:

```python
cfg.alpha.b
# -2

cfg.alpha.new_key = 42
cfg.alpha
# {"a": 10, "b": -2, "new_key": 42}
```

You can also use `deep_get` and `deep_set` to get/set deep content using [pydash](https://pydash.readthedocs.io/en/latest/) keys, useful if you don't know the keys at code time. The `deep_set` method also have a flag that disables the setting of the new value if this involves creating a new key.

```python
cfg.deep_get("alpha.b")
# -2

cfg.deep_set("alpha.new_key", 42)
cfg.deep_get("alpha")
# {"a": 10, "b": -2, "new_key": 42}

# This should be a NoOp, since "another_new_key" was not already present.
cfg.deep_set("alpha.another_new_key", 43, only_valid_keys=True)
cfg.deep_get("alpha")
# {"a": 10, "b": -2, "new_key": 42}
```

There is also a `deep_update` method to merge two configurations into one. The `full_merge` flag enables the setting on new keys.

```python
data = XConfig({
    "a": {"b": 100},
    "b": {"a": 1, "b": [{"a": -1, "b": -2}, "a"]},
})
other = XConfig({"b": {"b": [{"a": 42}], "c": {"a": 18, "b": 20}}})
data.deep_update(other)
# {
#     "a": {"b": 100},
#     "b": {"a": 1, "b": [{"a": 42, "b": -2}, "a"]},
# }

data.deep_update(other, full_merge=True)
# {
#     "a": {"b": 100},
#     "b": {"a": 1, "b": [{"a": 42, "b": -2}, "a"], "c": {"a": 18, "b": 20}}
# }
```

At any moment, you can convert the XConfig back to a dictionary by calling `to_dict`.

```python
plain_dict = cfg.to_dict()
type(plain_dict)
# dict
```

### I/O

`XConfig` provides a simplified interface to load/save from/to a file. The format is automatically inferred from the file extension.

```python
cfg = XConfig.from_file("path/to/my_cfg.yml")
cfg.save_to("another/path/to/my_cfg.json")
```


### Processing
At the moment of creation, the `XConfig` content will be an exact copy of the plain python dictionary used to create it, no check or operation is performed on the directives, they are treated just like any other string.

To "activate" them, you need to **process** the `XConfig`, by calling either `process` or `process_all`, passing an appropriate **context** dictionary.

`process` will compile and run the configuration **without branching** (i.e. sweeps nodes are disabled), and return the processed `XConfig`.

`process_all` will compile and run the configuration **with branching** and return a list of all the processed `XConfig`.

```python
cfg = XConfig.from_file("config.yml")

output = cfg.process()
outputs = cfg.process_all()
```

### Inspection
What if you just loaded an XConfig and are about to process it, only, you don't know what to pass as **context**, what environment variables are required, or what files are going to be imported. You can use the `inspect` method, to get some info on the `XConfig` that you are about to process.

The result of `inspect` is an `Inspection`, containing the following fields:
- `imports` - A `set` of all the absolute paths imported from the inspected `XConfig`.
- `variables` - An uninitialized structure that can be used as context, containing all variables and loop iterables, and their default value if present (`None` otherwise).
- `environ` - An uninitialized structure containing all environment variables and their default value if present (`None` otherwise).
- `symbols` - The `set` of all dynamically imported python files/modules.
- `processed` - A `bool` value that is true if the `XConfig` contains any **Choixe directive** and thus needs processing.

### Validation

At the moment of creation - whether from file or from a plain dictionary, you can specify an optional `Schema` object used for validation. More details [here](https://github.com/keleshev/schema). 

Validation is enabled only when a schema is set.

To validate an `XConfig` you can use `is_valid` to know if the configuration validates its schema. You can also use `validate` to perform full validation (enabling side effects).