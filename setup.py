from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pypdf-cli',
    version='0.1.0',
    author='Tobias Lass',
    author_email='tobi208@github.com',
    description='A Python-based CLI that allows for comfortable every-day PDF manipulation with PyPDF4.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tobi208/pypdf-cli",
    project_urls={
        "Bug Tracker": "https://github.com/tobi208/pypdf-cli/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    license='GNU General Public License v3 (GPLv3)',
    keywords=['pdf', 'cli', 'pypdf', 'click'],
    python_requires=">=3.6",
    install_requires=[
        'click>=8.0.3',
        'PyPDF4>=1.27.0',
    ],
    package_dir={"": "src"},
    py_modules=['pypdfcli'],
    entry_points={
        'console_scripts': [
            'pypdf-cli = pypdfcli:cli',
        ],
    },
)
