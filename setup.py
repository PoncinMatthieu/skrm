import os
import setuptools


def get_readme_content():
    with open("README.md", "r") as f:
        return f.read()


def get_package_version():
    locals = {}
    with open(os.path.join("skrm", "version.py")) as fd:
        exec(fd.read(), None, locals)
        return locals["__version__"]


setuptools.setup(
    name="skrm",
    version=get_package_version(),
    author="Matthieu Poncin",
    author_email="poncin.matthieu@gmail.com",
    description="Simple keyring manager - Allows you to store keys associated to tags into an encrypted file, using GPG.",
    long_description=get_readme_content(),
    long_description_content_type="text/markdown",
    url="https://github.com/PoncinMatthieu/skrm",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography"
    ],
    packages=setuptools.find_packages(include=["skrm", "skrm.*"]),
    entry_points={
        'console_scripts': [
            'skrm = skrm.__main__:keyring_manager.run'
            ],
        },
    test_suite="tests"
    )
