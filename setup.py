import setuptools
from glob import glob

with open("JEMViewer2/VERSION", "r") as f:
    version = f.readline()
 
setuptools.setup(
    name="JEMviewer2",
    version=version,
    install_requires=[
        "matplotlib",
        "numpy",
        "pandas",
        "PyQt6",
        "jupyter",
        "scipy",
        "natsort",
        "pyserial",
        "requests",
        "prettytable",
        "openpyxl",
    ],
    author="Hiraide",
    author_email="hiraide@cheme.kyoto-u.ac.jp",
    description="JEMViewer2",
    long_description="",
    packages=setuptools.find_packages(),
    data_files=[
        ('resources', glob('JEMViewer2/resources/*')),
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    include_package_data=True,
)