from setuptools import setup, find_packages

setup(
    name='archbyte',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'flask',
        'telethon',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
        
        ],
    },
    author='Arch Byte',
    author_email='cophtew@gmail.com',
    description='Telegram  , discord and Ai focused library ',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com//archbyte',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
