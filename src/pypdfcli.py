from ast import literal_eval
from os import makedirs
from os.path import basename, dirname

import click
from PyPDF4 import PdfFileReader, PdfFileWriter, PdfFileMerger
from PyPDF4.utils import PdfReadError
from pkg_resources import get_distribution


# Make custom Option classes to parse input

class ListOption(click.Option):

    def type_cast_value(self, ctx, values):
        return cast_values(cast_list, values)


class RangeOption(click.Option):

    def type_cast_value(self, ctx, values):
        return cast_values(cast_range, values)


class IndexOption(click.Option):

    def type_cast_value(self, ctx, values):
        return cast_values(cast_index, values)


def cast_values(cast_func, values):
    """
    Cast values according to a specified function.
    Catch trivial case and exceptions here.
    """

    if values is None:
        return set()
    try:
        return cast_func(values)
    except TypeError:
        raise click.BadParameter(values)
    except ValueError:
        raise click.BadParameter(values)
    except SyntaxError:
        raise click.BadParameter(values)


def cast_list(values):
    """
    Cast a cli list of str or Any to a python set of integer.
    """

    # values is an iterable because multiple is enabled
    parsed = []
    for value in values:

        # parse value with ast module
        # very sensitive process and likely to raise errors
        literal = literal_eval(value)

        # enforce list of integers
        if type(literal) != list or any(type(x) != int for x in literal):
            raise TypeError

        # decrease values by 1 to accommodate PyPDF
        parsed += [x - 1 for x in literal]

    # indices are unique
    return set(parsed)


def cast_range(values):
    """
    Cast a cli list of str or Any of length 2 to a python set of
    integer by decoding the input to a python range.
    """

    # values is an iterable because multiple is enabled
    parsed = []
    for value in values:

        # parse value with ast module
        # very sensitive process and likely to raise errors
        literal = literal_eval(value)

        # enforce list of integers with length 2 that encodes a range
        if type(literal) != list or len(literal) != 2:
            raise TypeError

        # decrease values by 1 to accommodate PyPDF
        # decode list to range and build list from it
        parsed += list(range(literal[0] - 1, literal[1]))

    # indices are unique
    return set(parsed)


def cast_index(values):
    """
    Cast a cli list of integers to a python set of integer.
    """

    # values is an iterable because multiple can be enabled
    # or a single integer because multiple can be disabled
    if type(values) == int:
        return values - 1

    # indices are unique
    return set(int(x) - 1 for x in values)


def generate_output_name(input_name, output_name, default):
    """
    Verify input/output file names and generate a default
    output file name if none was provided.
    """

    # verify input file
    if not input_name.endswith('.pdf'):
        raise click.BadParameter(message='Only .pdf files allowed.')

    # if output file was provided
    if output_name is not None:

        # verify output file
        if not output_name.endswith('.pdf'):
            raise click.BadParameter('Only .pdf files allowed.')

        # can't write output to input file because of PyPDF limitations
        if output_name == input_name:
            raise click.BadParameter('Cannot output to input file.')

        return output_name

    # otherwise auto generate output file name
    return basename(input_name)[:-4] + '_' + default + '.pdf'


def generate_selection(selection_sets, validation, non_empty=True):
    """
    Verify selection and sum selections up.
    """

    # sum selections up
    selection = set()
    for selection_set in selection_sets:
        selection |= selection_set

    # verify existence of any selection if required
    if non_empty and len(selection) == 0:
        raise click.BadParameter(message='No pages selected.')

    # verify selection by provided function
    if not all(map(validation, selection)):
        raise click.BadParameter(message='Invalid selection.')

    return selection


def validate_index(num_pages, lshift=0, rshift=0):
    """
    Create function that validates a selected index.
    An index is valid if it is an existing page number and
    within the specified left/right boundaries.
    """

    # verify specified boundaries
    if lshift < 0 or rshift < 0 or lshift + rshift >= num_pages:
        raise IndexError('Index shift must be within the range of existing pages and allow at least 1 selection.')

    # create validation function
    def f(x):
        return 0 + lshift <= x < num_pages - rshift

    return f


def buffer_number(max_digits, k):
    """
    Utility to buffer zeroes in front of a number
    according to the maximum amount of digits.
    """

    k = str(k)
    return '0' * (max_digits - len(k)) + k


def write(writer, output):
    """
    Write content to a specified output.
    Create directories if necessary.
    Overwrites existing files.
    """

    # create directories if necessary
    dirs = dirname(output)
    if len(dirs) > 0:
        makedirs(dirs, exist_ok=True)

    # write output
    with open(output, 'wb') as f:
        writer.write(f)


@click.group()
@click.version_option(get_distribution('pypdf-cli').version)
def cli():
    pass


OUTPUT_HELP = 'Optional location of the output pdf file. WARNING: overwrites existing files.'
LIST_HELP = 'List of indices. Enter list without spaces or wrap in quotation marks. E.g. [1,2,3] or \"[1, 2, 3]\"'
RANGE_HELP = 'Range of indices. Enter as list with 2 elements without spaces or wrap in quotation marks.' \
             ' E.g. [1,3] or \"[1, 3]\"'
INDEX_HELP = 'Single index. Enter an integer number.'
ALL_HELP = 'Select every index.'


def common_options(f):
    """
    Collect commonly used click Options.
    """

    f = click.argument('input-file', type=click.Path(exists=True))(f)
    f = click.option('--output', '-o', type=click.Path(dir_okay=True), help=OUTPUT_HELP)(f)
    f = click.option('--select-list', '-l', type=click.STRING, cls=ListOption, multiple=True, help=LIST_HELP)(f)
    f = click.option('--select-range', '-r', type=click.STRING, cls=RangeOption, multiple=True, help=RANGE_HELP)(f)
    f = click.option('--select-index', '-i', type=click.INT, cls=IndexOption, multiple=True, help=INDEX_HELP)(f)
    return f


@click.command()
@common_options
def delete(input_file, output, select_list, select_range, select_index):
    """
    Delete a selection of pages from a pdf file.

    INPUT_FILE is the location of the pdf file you wish to delete pages from.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'deleted')
    reader = PdfFileReader(open(input_file, 'rb'))
    selection = generate_selection([select_list, select_range, select_index], validate_index(reader.numPages))
    writer = PdfFileWriter()

    # specific verification
    retain = [i for i in range(reader.numPages) if i not in selection]
    if len(retain) == 0:
        reader.stream.close()
        raise click.BadParameter(message='Cannot delete all pages.')

    # build output
    for i in retain:
        writer.addPage(reader.getPage(i))

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@common_options
def extract(input_file, output, select_list, select_range, select_index):
    """
    Extract a selection of pages from a pdf file.

    INPUT_FILE is the location of the pdf file you wish to extract pages from.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'extracted')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    selection = generate_selection([select_list, select_range, select_index], validate_index(reader.numPages))
    writer = PdfFileWriter()

    # specific verification
    if len(selection) == reader.numPages:
        reader.stream.close()
        raise click.BadParameter(message='Cannot extract all pages.')

    # build output
    for i in selection:
        writer.addPage(reader.getPage(i))

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@click.argument('input-files', nargs=2, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--select-index', '-i', type=click.INT, cls=IndexOption, required=True, help=INDEX_HELP)
def insert(input_files, output, select_index):
    """
    Insert a second pdf file into a pdf file at a specified index.
    The new pdf file will contain the second file's pages starting at the index.

    INPUT_FILES 1. is the location of the pdf file you want to insert the second into.
    INPUT_FILES 2. is the location of the pdf file you want to insert into the first.
    """

    # configure and verify
    output = generate_output_name(input_files[0], output, 'inserted')
    try:
        reader1 = PdfFileReader(open(input_files[0], 'rb'))
        reader2 = PdfFileReader(open(input_files[1], 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')

    index = generate_selection([set(select_index)], validate_index(reader1.numPages)).pop()
    writer = PdfFileWriter()

    # build output
    for i in range(0, index):
        writer.addPage(reader1.getPage(i))
    for page in reader2.pages:
        writer.addPage(page)
    for i in range(index, reader1.numPages):
        writer.addPage(reader1.getPage(i))

    # finalize
    write(writer, output)
    reader1.stream.close()
    reader2.stream.close()


@click.command()
@click.argument('input-files', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
def merge(input_files, output):
    """
    Merge two or more pdf files.
    Files are appended in the order they are entered.

    INPUT_FILES are the locations of at least two pdf files to be merged.
    """

    # specific verification
    if len(input_files) < 2:
        raise click.BadParameter(message='Cannot merge less than two files.')

    # configure
    output = generate_output_name(input_files[0], output, 'merged')
    merger = PdfFileMerger()

    # build output
    for file in input_files:
        try:
            merger.append(open(file, 'rb'))
        except PdfReadError:
            merger.close()
            raise click.BadParameter('File cannot be read.')

    # finalize
    write(merger, output)
    merger.close()


@click.command()
@common_options
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
def split(input_file, output, select_list, select_range, select_index, all):
    """
    Split a pdf file at specified indices.
    The file is split AFTER a specified index. E.g. pages = {1, 2, 3, 4} and indices = [2, 3]
    results in {1, 2}, {3}, and {4}. That means an index needs to be
    lower than the number of pages.
    The output files are numerated as <output>_1.pdf, <output>_2.pdf, etc.

    INPUT_FILE is the location of the pdf file you want to split.
    """

    # configure
    output = generate_output_name(input_file, output, 'split')
    output = output[:-4] + '_'
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')

    # specific verification
    if reader.numPages < 2:
        reader.stream.close()
        raise click.BadParameter(message="Cannot split a file with less than two pages.")

    # if 'all' flag is set split at every index
    # requires selection to be a sorted list
    selection = list(range(reader.numPages - 1)) if all else sorted(list(
        generate_selection([select_list, select_range, select_index], validate_index(reader.numPages, rshift=1))
    ))

    # calculate splits that will make up the outputs
    splits = []
    for i, sel in enumerate(selection):
        # indices are inclusive so shift by 1
        # build range from previous selection to current selection
        splits.append(list(
            range(0, sel + 1) if i == 0 else
            range(selection[i - 1] + 1, sel + 1))
        )

    # include pages from last selection to end of pages
    splits.append(list(range(selection[-1] + 1, reader.numPages)))
    reader.stream.close()

    # track number of splits for output names
    max_digits = len(str(len(selection)))
    k = 1

    # build outputs
    # recreate reader for each writer because of a PyPDF bug
    # https://stackoverflow.com/questions/40168027
    for pages in splits:
        writer = PdfFileWriter()
        reader = PdfFileReader(open(input_file, 'rb'))
        for p in pages:
            writer.addPage(reader.getPage(p))
        write(writer, output + buffer_number(max_digits, k) + '.pdf')
        k += 1
        reader.stream.close()


@click.command()
@click.argument('input-file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--user-password', type=click.STRING, required=True,
              help='Allows for opening and reading the PDF file with the restrictions provided.')
@click.option('--owner-password', type=click.STRING,
              help='Allows for opening the PDF files without any restrictions. \
               By default, the owner password is the same as the user password.')
@click.option('--use-40bit', is_flag=True, default=False,
              help='Whether to use 40bit encryption. When false, 128bit encryption will be used.')
def encrypt(input_file, output, user_password, owner_password, use_40bit):
    """
    Encrypt a pdf file with a user and optional owner password.
    If no owner password is passed, it is the same as the user password.

    INPUT_FILE is the location of the pdf file you wish to encrypt.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'encrypted')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # specific verification
    if reader.isEncrypted:
        reader.stream.close()
        raise click.BadArgumentUsage(message='File is already encrypted.')

    # build output
    writer.appendPagesFromReader(reader)
    writer.encrypt(user_pwd=user_password, owner_pwd=owner_password, use_128bit=not use_40bit)

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@click.argument('input-file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--password', type=click.STRING, required=True, help='The password to match.')
def decrypt(input_file, output, password):
    """
    Decrypt a pdf file with a password.

    INPUT_FILE is the location of the pdf file you wish to decrypt.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'decrypted')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # specific verification
    if not reader.isEncrypted:
        reader.stream.close()
        raise click.BadArgumentUsage(message='File is not encrypted.')

    # build output
    success = reader.decrypt(password) > 0
    if success:
        writer.appendPagesFromReader(reader)
    else:
        reader.stream.close()
        raise click.BadParameter(message='Wrong password.')

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@click.argument('input-file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--images', is_flag=True, default=False, help='Whether to remove images.')
@click.option('--links', is_flag=True, default=False, help='Whether to remove links.')
@click.option('--text', is_flag=True, default=False, help='Whether to remove text.')
def remove(input_file, output, images, links, text):
    """
    Remove images, links, or text from a pdf file.

    INPUT_FILE is the location of the pdf file you wish to remove images, links, or text from.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'removed')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # specific verification
    if not any([images, links, text]):
        reader.stream.close()
        raise click.BadParameter(message='No objects to remove specified.')

    # build output
    writer.appendPagesFromReader(reader)
    if images:
        writer.removeImages()
    if links:
        writer.removeLinks()
    if text:
        writer.removeText()

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@click.argument('input-file', type=click.Path(exists=True))
def info(input_file):
    """
    Print information about a pdf file.

    INPUT_FILE is the location of the pdf file you wish to get information of.
    """

    # configure and verify
    generate_output_name(input_file, None, 'info')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')

    # build output
    for k, v in reader.documentInfo.items():
        click.echo(f'{k}: {v}')

    # finalize
    reader.stream.close()


@click.command()
@click.argument('input-file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
def reverse(input_file, output):
    """
    Reverse the pages of a pdf file.

    INPUT_FILE is the location of the pdf file you wish to reverse.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'reversed')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # build output
    for i in reversed(list(range(reader.getNumPages()))):
        writer.addPage(reader.getPage(i))

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@common_options
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
@click.option('--angle', type=click.INT, required=True,
              help='Angle to rotate pages clockwise. Must be increment of 90.')
def rotate(input_file, output, select_list, select_range, select_index, all, angle):
    """
    Rotate the pages of a pdf file.

    INPUT_FILE is the location of the pdf file you wish to rotate.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'rotated')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # if 'all' flag is set rotate every page
    selection = list(range(reader.numPages)) if all else list(
        generate_selection([select_list, select_range, select_index], validate_index(reader.numPages))
    )

    # specific verification
    if angle % 90 != 0:
        reader.stream.close()
        raise click.BadParameter('Rotation angle must be increment of 90.')

    # build output
    writer.appendPagesFromReader(reader)
    for i in selection:
        writer.getPage(i).rotateClockwise(angle)

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@common_options
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
@click.option('--scale-to', is_flag=True, default=False,
              help='Whether to change width and height of pages to a flat value.')
@click.option('--horizontal', type=click.FLOAT, required=True,
              help='Horizontal factor or value to scale pages by or to.')
@click.option('--vertical', type=click.FLOAT, required=True,
              help='Vertical factor or value to scale pages by or to.')
def scale(input_file, output, select_list, select_range, select_index, all, scale_to, horizontal, vertical):
    """
    Scale the pages of a pdf file.
    Uses scaleBy by default. Use --scale-to to scale to a flat value.

    INPUT_FILE is the location of the pdf file you wish to scale.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'scaled')
    try:
        reader = PdfFileReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfFileWriter()

    # if 'all' flag is set rotate every page
    selection = list(range(reader.numPages)) if all else list(
        generate_selection([select_list, select_range, select_index], validate_index(reader.numPages))
    )

    # build output
    writer.appendPagesFromReader(reader)
    for i in selection:
        if scale_to:
            writer.getPage(i).scaleTo(horizontal, vertical)
        else:
            writer.getPage(i).scale(horizontal, vertical)

    # finalize
    write(writer, output)
    reader.stream.close()


# finalize commands
cli.add_command(delete)
cli.add_command(extract)
cli.add_command(insert)
cli.add_command(merge)
cli.add_command(split)
cli.add_command(encrypt)
cli.add_command(decrypt)
cli.add_command(remove)
cli.add_command(info)
cli.add_command(reverse)
cli.add_command(rotate)
cli.add_command(scale)
