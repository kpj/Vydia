from setuptools import setup, find_packages


with open('README.md', encoding='utf-8') as fd:
    long_description = fd.read()

setup(
    name='vydia',
    version='0.0.1',

    description='A modularized video player with resume function',
    long_description=long_description,

    url='https://github.com/kpj/Vydia',

    author='kpj',
    author_email='kpjkpjkpjkpjkpjkpj@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video :: Display',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ],

    keywords='vydia video playback',
    packages=find_packages(exclude=['tests']),

    install_requires=['pafy', 'urwid', 'mpv>=0.1'],
    dependency_links=['https://github.com/jaseg/python-mpv/tarball/master#egg=mpv-0.1'],

    entry_points={
        'console_scripts': [
            'vydia=vydia:main',
        ],
    }
)