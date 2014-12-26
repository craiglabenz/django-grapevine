import os
import re
import sys
from setuptools import setup


# Borrowed from the infamous
# https://github.com/tomchristie/django-rest-framework/blob/master/setup.py
def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


# Borrowed from the infamous
# https://github.com/tomchristie/django-rest-framework/blob/master/setup.py
def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


# Borrowed from the infamous
# https://github.com/tomchristie/django-rest-framework/blob/master/setup.py
def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


version = get_version('grapevine')


if sys.argv[-1] == 'publish-test':
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push origin master")
    os.system("git push --tags")
    os.system("python setup.py sdist upload -r pypitest")
    sys.exit()


CLASSIFIERS = [
    "Framework :: Django",
    "Intended Audience :: Developers",
    "Programming Language :: Python",
]

INSTALL_REQUIRES = [
    "tablets==0.4.3",
    "html2text",
    "requests",
]

setup(
    name="django-grapevine",
    packages=get_packages("grapevine"),
    package_data=get_package_data("grapevine"),
    version=version,
    description="A comprehensive email tool for Django",
    url="https://github.com/craiglabenz/django-grapevine",
    download_url="https://github.com/craiglabenz/django-grapevine/tarball/{0}".format(version),
    keywords=["django", "email", "sending", "tracking"],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    author="Craig Labenz",
    author_email="craig.labenz@gmail.com",
    license="MIT"
)
