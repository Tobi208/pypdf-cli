from os.path import abspath, join

import pytest
from click.testing import CliRunner

from pypdf_cli import *

TEST_DIR = dirname(abspath(__file__))
TEST_FILE = join(TEST_DIR, 'file.pdf')

RUNNER = CliRunner()
TEST_OUT = join(TEST_DIR, 'test.pdf')


def test_generate_output_name():
    with pytest.raises(click.BadParameter):
        generate_output_name('missing extension', 'missing extension', 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('missing extension', None, 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('correct.pdf', 'missing extension', 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('missing extension', 'correct.pdf', 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('wrong extension.txt', 'wrong extension.txt', 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('wrong extension.txt', None, 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('correct.pdf', 'wrong extension.txt', 'default')
    with pytest.raises(click.BadParameter):
        generate_output_name('wrong extension.txt', 'correct.pdf', '')
    with pytest.raises(click.BadParameter):
        generate_output_name('same name.pdf', 'same name.pdf', '')

    assert generate_output_name('input.pdf', 'output.pdf', 'default') == 'output.pdf'
    assert generate_output_name('in put.pdf', 'out put.pdf', 'default') == 'out put.pdf'
    assert generate_output_name('dir/in put.pdf', 'output.pdf', 'default') == 'output.pdf'
    assert generate_output_name('dir/in put.pdf', None, 'default') == 'in put_default.pdf'
    assert generate_output_name('dir/in put.pdf', None, '') == 'in put_.pdf'


def test_generate_selection():
    def true(_):
        return True

    def false(_):
        return False

    def even(x):
        return x % 2 == 0

    with pytest.raises(click.BadParameter):
        generate_selection([], true)
    with pytest.raises(click.BadParameter):
        generate_selection([set()], true)
    with pytest.raises(click.BadParameter):
        generate_selection([set(), set()], true)
    with pytest.raises(click.BadParameter):
        generate_selection([], false)
    with pytest.raises(click.BadParameter):
        generate_selection([{1}], false)
    with pytest.raises(click.BadParameter):
        generate_selection([{1, 2, 3}], even)
    with pytest.raises(click.BadParameter):
        generate_selection([{2, 4}, {5}], even)
    with pytest.raises(click.BadParameter):
        generate_selection([{1, 2}], even)
    with pytest.raises(click.BadParameter):
        generate_selection([], even)

    assert generate_selection([], true, non_empty=False) == set()
    assert generate_selection([{1}], true) == {1}
    assert generate_selection([{1}, {2}], true) == {1, 2}
    assert generate_selection([{1, 2}, {3}], true) == {1, 2, 3}
    assert generate_selection([{1, 2}, set()], true) == {1, 2}
    assert generate_selection([{2}], even) == {2}
    assert generate_selection([{2, 4}], even) == {2, 4}
    assert generate_selection([{2}, set()], even) == {2}
    assert generate_selection([[{2, 4}, {8}], {6}], even) == {2, 4, 6, 8}


def test_validate_index():
    num_pages = 10
    pages = list(range(num_pages))

    with pytest.raises(IndexError):
        validate_index(num_pages, rshift=-1)
    with pytest.raises(IndexError):
        validate_index(num_pages, lshift=-1)
    with pytest.raises(IndexError):
        validate_index(num_pages, lshift=10)
    with pytest.raises(IndexError):
        validate_index(num_pages, lshift=5, rshift=5)

    f = validate_index(num_pages)
    assert all(f(page) for page in pages)

    f = validate_index(num_pages, lshift=1)
    assert all(f(page) for page in pages[1:])
    assert not f(0)

    f = validate_index(num_pages, rshift=1)
    assert all(f(page) for page in pages[:-1])
    assert not f(9)

    f = validate_index(num_pages, lshift=1, rshift=1)
    assert all(f(page) for page in pages[1:-1])
    assert not f(0)
    assert not f(9)

    f = validate_index(num_pages, lshift=4, rshift=5)
    assert not any(f(page) for page in pages if page != 4)
    assert f(4)

    f = validate_index(num_pages, rshift=9)
    assert not any(f(page) for page in pages[1:])
    assert f(0)


def test_buffer_number():
    assert buffer_number(1, 1) == '1'
    assert buffer_number(2, 1) == '01'
    assert buffer_number(3, 1) == '001'
    assert buffer_number(0, 1) == '1'


def test_convert_list():
    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-l', '1,a'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-l', '1,2.0'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-l', '1'])
    assert result.exit_code == 0

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-l', '1,2,3'])
    assert result.exit_code == 0


def test_convert_range():
    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1-a'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1-2.0'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1-2-3'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1,2'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1-2'])
    assert result.exit_code == 0


def test_convert_int():
    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-i', 'a'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-i', '2.0'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-i', '1'])
    assert result.exit_code == 0


def test_delete():
    # result.exit_code = 0 -> okay
    # result.exit_code = 2 -> error raised

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-i', '1'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 2}')

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-l', '1,2,3,4'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 5}')

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '10-12'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '10-12', '-l', '1,2,3,4'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 5}')

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '5-10'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(4):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(4, 6):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 7}')

    RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '5-10', '-i', '1'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(3):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 2}')
    for i in range(3, 5):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 8}')

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '1-12'])
    assert result.exit_code == 2

    result = RUNNER.invoke(delete, [TEST_FILE, '-o', TEST_OUT, '-r', '2-12', '-i', '1'])
    assert result.exit_code == 2


def test_extract():
    # result.exit_code = 0 -> okay
    # result.exit_code = 2 -> error raised

    RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-i', '1'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    assert len(res_reader.pages) == 1
    assert res_reader.pages[0].extract_text().startswith('page1')

    RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-l', '1,2,3,4'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    assert len(res_reader.pages) == 4
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')

    RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-r', '10-12'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    assert len(res_reader.pages) == 3
    for i in range(len(res_reader.pages)):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 10}')

    RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-r', '10-12', '-l', '1,2,3,4'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    assert len(res_reader.pages) == 7
    for i in range(4):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(4, 7):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 6}')

    RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-r', '5-10', '-i', '1'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    assert len(res_reader.pages) == 7
    assert res_reader.pages[0].extract_text().startswith('page1')
    for i in range(1, 7):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 4}')

    result = RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-r', '1-12'])
    assert result.exit_code == 2

    result = RUNNER.invoke(extract, [TEST_FILE, '-o', TEST_OUT, '-r', '2-12', '-i', '1'])
    assert result.exit_code == 2


def test_insert():
    # result.exit_code = 0 -> okay
    # result.exit_code = 2 -> error raised

    RUNNER.invoke(insert, [TEST_FILE, TEST_FILE, '-o', TEST_OUT, '-i', '1'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(0, 12):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(12, 24):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 11}')

    RUNNER.invoke(insert, [TEST_FILE, TEST_FILE, '-o', TEST_OUT, '-i', '13'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(0, 12):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(12, 24):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 11}')

    RUNNER.invoke(insert, [TEST_FILE, TEST_FILE, '-o', TEST_OUT, '-i', '6'])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(0, 5):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(5, 17):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 4}')
    for i in range(17, 24):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 11}')


def test_merge():
    # result.exit_code = 0 -> okay
    # result.exit_code = 2 -> error raised

    RUNNER.invoke(merge, [TEST_FILE, TEST_FILE, '-o', TEST_OUT])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(0, 12):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(12, 24):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 11}')

    RUNNER.invoke(merge, [TEST_FILE, TEST_FILE, TEST_FILE, '-o', TEST_OUT])
    res_reader = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(0, 12):
        assert res_reader.pages[i].extract_text().startswith(f'page{i + 1}')
    for i in range(12, 24):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 11}')
    for i in range(24, 36):
        assert res_reader.pages[i].extract_text().startswith(f'page{i - 23}')

    result = RUNNER.invoke(merge, [TEST_FILE, '-o', TEST_OUT])
    assert result.exit_code == 2


def test_split():
    RUNNER.invoke(split, [TEST_FILE, '-o', TEST_OUT, '-i', '3'])
    test_out_base = TEST_OUT[:-4]
    res1 = PdfReader(open(test_out_base + '_1.pdf', 'rb'))
    for i in range(0, 3):
        assert res1.pages[i].extract_text().startswith(f'page{i + 1}')
    res2 = PdfReader(open(test_out_base + '_2.pdf', 'rb'))
    for i in range(0, 9):
        assert res2.pages[i].extract_text().startswith(f'page{i + 4}')

    RUNNER.invoke(split, [TEST_FILE, '-o', TEST_OUT, '-l', '3,9'])
    test_out_base = TEST_OUT[:-4]
    res1 = PdfReader(open(test_out_base + '_1.pdf', 'rb'))
    for i in range(0, 3):
        assert res1.pages[i].extract_text().startswith(f'page{i + 1}')
    res2 = PdfReader(open(test_out_base + '_2.pdf', 'rb'))
    for i in range(0, 6):
        assert res2.pages[i].extract_text().startswith(f'page{i + 4}')
    res3 = PdfReader(open(test_out_base + '_3.pdf', 'rb'))
    for i in range(0, 3):
        assert res3.pages[i].extract_text().startswith(f'page{i + 10}')

    RUNNER.invoke(split, [TEST_FILE, '-o', TEST_OUT, '-a'])
    test_out_base = TEST_OUT[:-4]
    for i in range(1, 13):
        res = PdfReader(open(test_out_base + f'_{buffer_number(2, i)}.pdf', 'rb'))
        assert res.pages[0].extract_text().startswith(f'page{i}')

    result = RUNNER.invoke(split, [test_out_base + '_01.pdf', '-o', TEST_OUT, '-i', '1'])
    assert result.exit_code == 2


def test_encrypt():
    RUNNER.invoke(encrypt, [TEST_FILE, '-o', TEST_OUT, '--user-password', '1234', '--owner-password', 'abcd'])
    res = PdfReader(open(TEST_OUT, 'rb'))
    assert res.is_encrypted
    with pytest.raises(PdfReadError):
        res.pages[0]
    assert res.decrypt('wrong pw') == 0
    assert res.decrypt('1234') == 1
    assert res.decrypt('abcd') == 2
    assert len(res.pages) == 12


def test_decrypt():
    test_out_encrypted = TEST_OUT[:-4] + '_encrypted.pdf'
    RUNNER.invoke(encrypt, [TEST_FILE, '-o', test_out_encrypted, '--user-password', '1234', '--owner-password', 'abcd'])

    RUNNER.invoke(decrypt, [test_out_encrypted, '-o', TEST_OUT, '--password', '1234'])
    res = PdfReader(open(TEST_OUT, 'rb'))
    assert not res.is_encrypted

    RUNNER.invoke(decrypt, [test_out_encrypted, '-o', TEST_OUT, '--password', 'abcd'])
    res = PdfReader(open(TEST_OUT, 'rb'))
    assert not res.is_encrypted

    result = RUNNER.invoke(decrypt, [test_out_encrypted, '-o', TEST_OUT, '--password', 'wrong pw'])
    assert result.exit_code == 2

    result = RUNNER.invoke(decrypt, [TEST_FILE, '-o', TEST_OUT, '--password', 'wrong pw'])
    assert result.exit_code == 2


def test_remove():
    result = RUNNER.invoke(remove, [TEST_FILE, '-o', TEST_OUT])
    assert result.exit_code == 2

    RUNNER.invoke(remove, [TEST_FILE, '-o', TEST_OUT, '--text'])
    res = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res.pages)):
        assert res.pages[i].extract_text().strip() == ''

    # I don't know how to test removal of images and links
    # PyPDF4 doesn't appear to have a high level api for that


def test_info():
    result = RUNNER.invoke(info, [TEST_FILE])
    assert result.exit_code == 0
    assert len(result.output) > 0

    # not sure how to test the content of the document info


def test_reverse():
    RUNNER.invoke(reverse, [TEST_FILE, '-o', TEST_OUT])
    res = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res.pages)):
        assert res.pages[i].extract_text().startswith(f'page{12 - i}')


def test_rotate():
    RUNNER.invoke(rotate, [TEST_FILE, '-o', TEST_OUT, '-a', '--angle', 90])
    res = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res.pages)):
        page = res.pages[i]
        rotate_obj = page.get("/Rotate", 0)
        current_angle = rotate_obj if isinstance(rotate_obj, int) else rotate_obj.getObject()
        assert current_angle == 90

    RUNNER.invoke(rotate, [TEST_FILE, '-o', TEST_OUT, '-a', '--angle', -90])
    res = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(len(res.pages)):
        page = res.pages[i]
        rotate_obj = page.get("/Rotate", 0)
        current_angle = rotate_obj if isinstance(rotate_obj, int) else rotate_obj.getObject()
        assert current_angle == -90

    RUNNER.invoke(rotate, [TEST_FILE, '-o', TEST_OUT, '-r', '1-6', '--angle', 90])
    res = PdfReader(open(TEST_OUT, 'rb'))
    for i in range(6):
        page = res.pages[i]
        rotate_obj = page.get("/Rotate", 0)
        current_angle = rotate_obj if isinstance(rotate_obj, int) else rotate_obj.getObject()
        assert current_angle == 90
    for i in range(6, 12):
        page = res.pages[i]
        rotate_obj = page.get("/Rotate", 0)
        current_angle = rotate_obj if isinstance(rotate_obj, int) else rotate_obj.getObject()
        assert current_angle == 0

    result = RUNNER.invoke(rotate, [TEST_FILE, '-o', TEST_OUT, '-a', '--angle', 45])
    assert result.exit_code == 2


def test_scale():
    result = RUNNER.invoke(scale, [TEST_FILE, '-o', TEST_OUT, '-a', '--vertical', 2.0, '--horizontal', 2.0])
    assert result.exit_code == 0

    result = RUNNER.invoke(scale, [TEST_FILE, '-o', TEST_OUT, '-r', '1-6', '--vertical', 2.0, '--horizontal', 2.0])
    assert result.exit_code == 0

    result = RUNNER.invoke(scale, [TEST_FILE, '-o', TEST_OUT, '-a', '--vertical', 256.0, '--horizontal', 256.0,
                                   '--scale-to'])
    assert result.exit_code == 0

    # I don't know how to test the size of pages
    # PyPDF4 doesn't appear to have a high level api for that
