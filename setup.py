from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="archbyte",
    version="0.1.0",
    author="Cyrus Arch",
    author_email="server.arch@tuta.io",
    description="A Python library for Telegram automation and group management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xcophtew/archbyte",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "telethon>=1.24.0",
    ],
    keywords="telegram automation bot group management spam-detection",
    project_urls={
        "Bug Reports": "https://github.com/xcophtew/archbyte/issues",
        "Source": "https://github.com/xcophtew/archbyte",
    },
)