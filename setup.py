# -*- coding: utf-8 -*-
import os
import io
from setuptools import setup, find_packages


# Helpers
def read(*paths):
    """Read a text file."""
    basedir = os.path.dirname(__file__)
    full_path = os.path.join(basedir, *paths)
    contents = io.open(full_path, encoding='utf-8').read().strip()
    return contents


# Prepare
PACKAGE = 'open_captcha'
NAME = PACKAGE.replace('_', '-')
INSTALL_REQUIRES = [
    'numpy',
    'matplotlib',
    'pandas',
    'python-Levenshtein'
]
TESTS_REQUIRE = [
    'tox',
    'pylama',
]
README = read('README.md')
VERSION = read(PACKAGE, 'VERSION')
PACKAGES = find_packages(exclude=['tests', 'docs'])


# Run
setup(
    name=NAME,
    version=VERSION,
    packages=PACKAGES,
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require={'develop': TESTS_REQUIRE},
    long_description=README,
    description='CAPTCHA challenges generated from your service\'s data',
    author='Hasadna',
    author_email='info@hasadna.org.il',
    url='https://www.hasadna.org.il',
    license='MIT',
    keywords=[
        'CAPTCHA',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
