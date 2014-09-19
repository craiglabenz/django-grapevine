import os
from distutils.core import setup

from grapevine import __version__


CLASSIFIERS = [
    "Framework :: Django",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
]

INSTALL_REQUIRES = [
    "tablets",
    "html2text",
    "requests",
]

setup(
    name="django-grapevine",
    packages=["grapevine"],
    version=__version__,
    description="A comprehensive email tool for Django",
    url="https://github.com/craiglabenz/django-grapevine",
    download_url="https://github.com/craiglabenz/django-grapevine/tarball/{0}".format(__version__),
    keywords=["django", "email", "sending", "tracking"],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    author="Craig Labenz",
    author_email="craig.labenz@gmail.com",
    license="MIT"
)
