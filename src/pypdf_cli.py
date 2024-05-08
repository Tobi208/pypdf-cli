from os import makedirs, listdir, getcwd
from os.path import basename, dirname

import click
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


# auxiliary functions

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


def validate_selection(selection, validation, non_empty=True):
    """
    Validate selection given a selection and validation method.
    """

    # verify existence of any selection if required
    if non_empty and (selection is None or len(selection) == 0):
        raise click.BadParameter(message='No pages selected.')

    # verify selection by provided function
    if not all(map(validation, selection)):
        raise click.BadParameter(message=f'Invalid selection: {sorted([s + 1 for s in selection])!r}')

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


# click functions

@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option()
def cli():
    pass


# Make custom Option classes to parse input
# Decrement user indices to match PyPDF indices

class PagesType(click.ParamType):
    
    name = "INT PAGES"

    def convert(self, value, param, ctx):

        try:
            selection = set()
            for c_split in value.replace(' ', '').split(','):
                if '-' in c_split:
                    r_split = c_split.split('-')
                    assert len(r_split) == 2
                    selection.update(range(int(r_split[0]) - 1, int(r_split[1])))
                else:
                    selection.add(int(c_split) - 1)
        except (ValueError, AssertionError):
            self.fail(f'{value!r} is not a valid selection of integers. Use as 1,3-5,7.', param, ctx)

        return selection

INT_PAGES = PagesType()

OUTPUT_HELP = 'Optional location of the output pdf file. WARNING: overwrites existing files.'
PAGES_MULTI_HELP = 'Selection of pages. Enter list of integers and ranges without spaces or wrap in quotation marks. E.g. 1,3-5,7.'
PAGES_SINGLE_HELP = 'Selection of page. Enter integer. E.g. 2.'
ALL_HELP = 'Select every index.'


def common_options(f):
    """
    Collect commonly used click Options.
    """

    f = click.argument('input-file', type=click.Path(exists=True))(f)
    f = click.option('--output', '-o', type=click.Path(dir_okay=True), help=OUTPUT_HELP)(f)
    f = click.option('--select-pages', '-p', type=INT_PAGES, multiple=False, help=PAGES_MULTI_HELP)(f)
    return f


# commands

@click.command()
@common_options
def delete(input_file, output, select_pages):
    """
    Delete a selection of pages from a pdf file.

    INPUT_FILE is the location of the pdf file you wish to delete pages from.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'deleted')
    reader = PdfReader(open(input_file, 'rb'))
    selection = validate_selection(select_pages, validate_index(len(reader.pages)))
    writer = PdfWriter()

    # specific verification
    retain = [i for i in range(len(reader.pages)) if i not in selection]
    if len(retain) == 0:
        reader.stream.close()
        raise click.BadParameter(message='Cannot delete all pages.')

    # build output
    for i in retain:
        writer.add_page(reader.pages[i])

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@common_options
def extract(input_file, output, select_pages):
    """
    Extract a selection of pages from a pdf file.

    INPUT_FILE is the location of the pdf file you wish to extract pages from.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'extracted')
    try:
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    selection = validate_selection(select_pages, validate_index(len(reader.pages)))
    writer = PdfWriter()

    # specific verification
    if len(selection) == len(reader.pages):
        reader.stream.close()
        raise click.BadParameter(message='Cannot extract all pages.')

    # build output
    for i in selection:
        writer.add_page(reader.pages[i])

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@click.argument('input-files', nargs=2, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--select-pages', '-p', type=INT_PAGES, required=True, multiple=False, help=PAGES_SINGLE_HELP)
def insert(input_files, output, select_pages):
    """
    Insert a second pdf file into a pdf file at a specified index.
    The new pdf file will contain the second file's pages starting at the index.

    INPUT_FILES 1. is the location of the pdf file you want to insert the second into.
    INPUT_FILES 2. is the location of the pdf file you want to insert into the first.
    """

    # configure and verify
    output = generate_output_name(input_files[0], output, 'inserted')
    try:
        reader1 = PdfReader(open(input_files[0], 'rb'))
        reader2 = PdfReader(open(input_files[1], 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    selection = validate_selection(select_pages, validate_index(len(reader1.pages)))
    index = selection.pop()
    writer = PdfWriter()

    # build output
    for i in range(0, index):
        writer.add_page(reader1.pages[i])
    for page in reader2.pages:
        writer.add_page(page)
    for i in range(index, len(reader1.pages)):
        writer.add_page(reader1.pages[i])

    # finalize
    write(writer, output)
    reader1.stream.close()
    reader2.stream.close()


@click.command()
@click.argument('input-files', nargs=-1, type=click.Path(exists=True), required=False)
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_HELP)
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
def merge(input_files, output, all):
    """
    Merge two or more pdf files.
    Files are appended in the order they are entered.

    INPUT_FILES are the locations of at least two pdf files to be merged.
    Merge all files in the current directory if no input is given.
    """

    # if no input files are specified or 'all' flag is set,
    # take all pdf files in current directory
    if len(input_files) == 0 or all:
        input_files = [f for f in listdir(getcwd()) if f.endswith('.pdf')]

    # specific verification
    if len(input_files) < 2:
        raise click.BadParameter(message='Cannot merge less than two files.')

    # configure
    output = generate_output_name(input_files[0], output, 'merged')
    writer = PdfWriter()

    # build output
    for file in input_files:
        try:
            writer.append(open(file, 'rb'))
        except PdfReadError:
            writer.close()
            raise click.BadParameter('File cannot be read.')

    # finalize
    write(writer, output)
    writer.close()


@click.command()
@common_options
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
def split(input_file, output, select_pages, all):
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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')

    # specific verification
    if len(reader.pages) < 2:
        reader.stream.close()
        raise click.BadParameter(message="Cannot split a file with less than two pages.")

    # if 'all' flag is set split at every index
    # requires selection to be a sorted list
    if all:
        selection = list(range(len(reader.pages) - 1))
    else:
        selection = validate_selection(select_pages, validate_index(len(reader.pages), rshift=1))
        selection = sorted(list(selection))

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
    splits.append(list(range(selection[-1] + 1, len(reader.pages))))
    reader.stream.close()

    # track number of splits for output names
    max_digits = len(str(len(selection)))
    k = 1

    # build outputs
    # recreate reader for each writer because of a PyPDF bug
    # https://stackoverflow.com/questions/40168027
    for pages in splits:
        writer = PdfWriter()
        reader = PdfReader(open(input_file, 'rb'))
        for p in pages:
            writer.add_page(reader.pages[p])
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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # specific verification
    if reader.is_encrypted:
        reader.stream.close()
        raise click.BadArgumentUsage(message='File is already encrypted.')

    # build output
    writer.append_pages_from_reader(reader)
    writer.encrypt(user_password=user_password, owner_password=owner_password, use_128bit=not use_40bit)

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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # specific verification
    if not reader.is_encrypted:
        reader.stream.close()
        raise click.BadArgumentUsage(message='File is not encrypted.')

    # build output
    success = reader.decrypt(password) > 0
    if success:
        writer.append_pages_from_reader(reader)
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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # specific verification
    if not any([images, links, text]):
        reader.stream.close()
        raise click.BadParameter(message='No objects to remove specified.')

    # build output
    writer.append_pages_from_reader(reader)
    if images:
        writer.remove_images()
    if links:
        writer.remove_links()
    if text:
        writer.remove_text()

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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')

    # build output
    for k, v in reader.metadata.items():
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
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # build output
    for i in reversed(list(range(len(reader.pages)))):
        writer.add_page(reader.pages[i])

    # finalize
    write(writer, output)
    reader.stream.close()


@click.command()
@common_options
@click.option('--all', '-a', is_flag=True, default=False, help=ALL_HELP)
@click.option('--angle', type=click.INT, required=True,
              help='Angle to rotate pages clockwise. Must be increment of 90.')
def rotate(input_file, output, select_pages, all, angle):
    """
    Rotate a selection of pages of a pdf file.

    INPUT_FILE is the location of the pdf file you wish to rotate.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'rotated')
    try:
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # if 'all' flag is set rotate every page
    if all:
        selection = set(range(len(reader.pages)))
    else:
        selection = validate_selection(select_pages, validate_index(len(reader.pages)))

    # specific verification
    if angle % 90 != 0:
        reader.stream.close()
        raise click.BadParameter('Rotation angle must be increment of 90.')

    # build output
    writer.append_pages_from_reader(reader)
    for i in selection:
        writer.pages[i].rotate(angle)

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
def scale(input_file, output, select_pages, all, scale_to, horizontal, vertical):
    """
    Scale a selection of pages of a pdf file.
    Uses scaleBy by default. Use --scale-to to scale to a flat value.

    INPUT_FILE is the location of the pdf file you wish to scale.
    """

    # configure and verify
    output = generate_output_name(input_file, output, 'scaled')
    try:
        reader = PdfReader(open(input_file, 'rb'))
    except PdfReadError:
        raise click.BadParameter('File cannot be read.')
    writer = PdfWriter()

    # if 'all' flag is set rotate every page
    if all:
        selection = set(range(len(reader.pages)))
    else:
        selection = validate_selection(select_pages, validate_index(len(reader.pages)))

    # build output
    writer.append_pages_from_reader(reader)
    for i in selection:
        if scale_to:
            writer.pages[i].scale_to(horizontal, vertical)
        else:
            writer.pages[i].scale(horizontal, vertical)

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
