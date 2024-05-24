# `form16-parser`
Form 16 parser for TDS

[![](https://img.shields.io/static/v1?label=Licence&message=MIT&color=darkgreen)](https://github.com/INF800/form16-parser)
[![stability-alpha](https://img.shields.io/badge/stability-alpha-f4d03f.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#alpha)
[![](https://img.shields.io/static/v1?label=Python&message=>=3.10&color=indigo)](https://github.com/INF800/form16-parser) <img src="https://img.shields.io/github/stars/INF800/form16-parser.svg?style=social&" alt="GitHub stars">

[Live Demo (click here)](https://huggingface.co/spaces/arakesh/form16-parser)

### Usage:

Install the package using:

```
pip install git+https://github.com/INF800/form16-parser.git@e83ddad7e18b31f04cb454b3eea5b837ddb0a374#egg=form16_parser
```

And parse your Form 16 using:

```py
from pprint import pprint
from form16_parser import build_parser

filepath = "/path/to/pdf/file"

parser = build_parser()
parsed = parser.parse(filepath, return_output=True)

pprint(parsed)
```
