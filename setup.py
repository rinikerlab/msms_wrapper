from setuptools import setup

setup(
    name="msms wrapper",
    version="0.1",
    description="Python Wrapper for the 'msms' program to compute molecular surfaces.",
    author="Franz Waibl",
    author_email="franz.waibl@phys.chem.ethz.ch",
    install_requires=[],
    setup_requires=['pytest_runner'],
    tests_require=['pytest'],
    py_modules=['msms.wrapper'],
    packages=['msms'],
)
