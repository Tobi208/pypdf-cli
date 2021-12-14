# pypdf-cli

------------

This command line tool is based on [click](https://github.com/pallets/click) and [PyPDF4](https://github.com/claird/PyPDF4).
It allows access to most of PyPDF4's functionalities and adds other sensible functionalities.
The aim is to provide an OS-independent CLI that allows for comfortable every-day PDF manipulation.

## Download

Requires **python >= 3.6**

* Build locally:
  * Clone this repository
  * ``python -m pip -r requirements.txt``
  * test with ``pytest``
  * ``python -m build``

* Install from [PyPi](https://pypi.org/project/pypdf-cli/):
  * ``python -m pip install pypdf-cli``

## Usage

``pypdf-cli [OPTIONS] COMMAND [ARGS]...``

``pypdf-cli COMMAND --help`` to learn about a command's options.

| Command | Description                                                    |
|---------|----------------------------------------------------------------|
| decrypt | Decrypt a pdf file with a password.                            |
| delete  | Delete a selection of pages from a pdf file.                   |
| encrypt | Encrypt a pdf file with a user and optional owner password.    |
| extract | Extract a selection of pages from a pdf file.                  |
| info    | Print information about a pdf file.                            |
| insert  | Insert a second pdf file into a pdf file at a specified index. |
| merge   | Merge two or more pdf files.                                   |
| remove  | Remove images, links, or text from a pdf file.                 |
| reverse | Reverse the pages of a pdf file.                               |
| rotate  | Rotate a selection of pages of a pdf file.                     |
| scale   | Scale a selection of pages of a pdf file.                      |
| split   | Split a pdf file at specified indices.            

```
Usage: pypdf-cli decrypt [OPTIONS] INPUT_FILE

  Decrypt a pdf file with a password.

  INPUT_FILE is the location of the pdf file you wish to decrypt.

Options:
  -o, --output PATH  Optional location of the output pdf file. WARNING:
                     overwrites existing files.
  --password TEXT    The password to match.  [required]
  --help             Show this message and exit.
```

```
Usage: pypdf-cli delete [OPTIONS] INPUT_FILE

  Delete a selection of pages from a pdf file.

  INPUT_FILE is the location of the pdf file you wish to delete pages from.

Options:
  -i, --select-index INTEGER  Single index. Enter an integer number.
  -r, --select-range TEXT     Range of indices. Enter as list with 2 elements
                              without spaces or wrap in quotation marks. E.g.
                              [1,3] or "[1, 3]"
  -l, --select-list TEXT      List of indices. Enter list without spaces or
                              wrap in quotation marks. E.g. [1,2,3] or "[1, 2,
                              3]"
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  --help                      Show this message and exit.
```

```
Usage: pypdf-cli encrypt [OPTIONS] INPUT_FILE

  Encrypt a pdf file with a user and optional owner password. If no owner
  password is passed, it is the same as the user password.

  INPUT_FILE is the location of the pdf file you wish to encrypt.

Options:
  -o, --output PATH      Optional location of the output pdf file. WARNING:
                         overwrites existing files.
  --user-password TEXT   Allows for opening and reading the PDF file with the
                         restrictions provided.  [required]
  --owner-password TEXT  Allows for opening the PDF files without any
                         restrictions.                By default, the owner
                         password is the same as the user password.
  --use-40bit            Whether to use 40bit encryption. When false, 128bit
                         encryption will be used.
  --help                 Show this message and exit.
```

```
Usage: pypdf-cli extract [OPTIONS] INPUT_FILE

  Extract a selection of pages from a pdf file.

  INPUT_FILE is the location of the pdf file you wish to extract pages from.

Options:
  -i, --select-index INTEGER  Single index. Enter an integer number.
  -r, --select-range TEXT     Range of indices. Enter as list with 2 elements
                              without spaces or wrap in quotation marks. E.g.
                              [1,3] or "[1, 3]"
  -l, --select-list TEXT      List of indices. Enter list without spaces or
                              wrap in quotation marks. E.g. [1,2,3] or "[1, 2,
                              3]"
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  --help                      Show this message and exit.
```

```
Usage: pypdf-cli info [OPTIONS] INPUT_FILE

  Print information about a pdf file.

  INPUT_FILE is the location of the pdf file you wish to get information of.

Options:
  --help  Show this message and exit.
```

```
Usage: pypdf-cli insert [OPTIONS] INPUT_FILES...

  Insert a second pdf file into a pdf file at a specified index. The new pdf
  file will contain the second file's pages starting at the index.

  INPUT_FILES 1. is the location of the pdf file you want to insert the second
  into. INPUT_FILES 2. is the location of the pdf file you want to insert into
  the first.

Options:
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  -i, --select-index INTEGER  Single index. Enter an integer number.
                              [required]
  --help                      Show this message and exit.
```

```
Usage: pypdf-cli merge [OPTIONS] [INPUT_FILES]...

  Merge two or more pdf files. Files are appended in the order they are
  entered.

  INPUT_FILES are the locations of at least two pdf files to be merged.

Options:
  -o, --output PATH  Optional location of the output pdf file. WARNING:
                     overwrites existing files.
  --help             Show this message and exit.
```

```
Usage: pypdf-cli remove [OPTIONS] INPUT_FILE

  Remove images, links, or text from a pdf file.

  INPUT_FILE is the location of the pdf file you wish to remove images, links,
  or text from.

Options:
  -o, --output PATH  Optional location of the output pdf file. WARNING:
                     overwrites existing files.
  --images           Whether to remove images.
  --links            Whether to remove links.
  --text             Whether to remove text.
  --help             Show this message and exit.
```

```
Usage: pypdf-cli reverse [OPTIONS] INPUT_FILE

  Reverse the pages of a pdf file.

  INPUT_FILE is the location of the pdf file you wish to reverse.

Options:
  -o, --output PATH  Optional location of the output pdf file. WARNING:
                     overwrites existing files.
  --help             Show this message and exit.
```

```
Usage: pypdf-cli rotate [OPTIONS] INPUT_FILE

  Rotate a selection of pages of a pdf file.

  INPUT_FILE is the location of the pdf file you wish to rotate.

Options:
  -i, --select-index INTEGER  Single index. Enter an integer number.
  -r, --select-range TEXT     Range of indices. Enter as list with 2 elements
                              without spaces or wrap in quotation marks. E.g.
                              [1,3] or "[1, 3]"
  -l, --select-list TEXT      List of indices. Enter list without spaces or
                              wrap in quotation marks. E.g. [1,2,3] or "[1, 2,
                              3]"
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  -a, --all                   Select every index.
  --angle INTEGER             Angle to rotate pages clockwise. Must be
                              increment of 90.  [required]
  --help                      Show this message and exit.
```

```
Usage: pypdf-cli scale [OPTIONS] INPUT_FILE

  Scale a selection of pages of a pdf file. Uses scaleBy by default. Use
  --scale-to to scale to a flat value.

  INPUT_FILE is the location of the pdf file you wish to scale.

Options:
  -i, --select-index INTEGER  Single index. Enter an integer number.
  -r, --select-range TEXT     Range of indices. Enter as list with 2 elements
                              without spaces or wrap in quotation marks. E.g.
                              [1,3] or "[1, 3]"
  -l, --select-list TEXT      List of indices. Enter list without spaces or
                              wrap in quotation marks. E.g. [1,2,3] or "[1, 2,
                              3]"
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  -a, --all                   Select every index.
  --scale-to                  Whether to change width and height of pages to a
                              flat value.
  --horizontal FLOAT          Horizontal factor or value to scale pages by or
                              to.  [required]
  --vertical FLOAT            Vertical factor or value to scale pages by or
                              to.  [required]
  --help                      Show this message and exit.
```

```
Usage: pypdf-cli split [OPTIONS] INPUT_FILE

  Split a pdf file at specified indices. The file is split AFTER a specified
  index. E.g. pages = {1, 2, 3, 4} and indices = [2, 3] results in {1, 2},
  {3}, and {4}. That means an index needs to be lower than the number of
  pages. The output files are numerated as <output>_1.pdf, <output>_2.pdf,
  etc.

  INPUT_FILE is the location of the pdf file you want to split.

Options:
  -i, --select-index INTEGER  Single index. Enter an integer number.
  -r, --select-range TEXT     Range of indices. Enter as list with 2 elements
                              without spaces or wrap in quotation marks. E.g.
                              [1,3] or "[1, 3]"
  -l, --select-list TEXT      List of indices. Enter list without spaces or
                              wrap in quotation marks. E.g. [1,2,3] or "[1, 2,
                              3]"
  -o, --output PATH           Optional location of the output pdf file.
                              WARNING: overwrites existing files.
  -a, --all                   Select every index.
  --help                      Show this message and exit.
```|