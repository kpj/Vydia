from setuptools import setup, find_packages


setup(
    name='vydia',
    version='0.5.1',

    description='A modularized video player with resume function',

    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md',

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

    install_requires=[
        'appdirs', 'pafy', 'urwid', 'urwid_readline',
        'click', 'python-mpv', 'logzero'
    ],

    entry_points={
        'console_scripts': [
            'vydia=vydia:main',
        ],
    }
)
