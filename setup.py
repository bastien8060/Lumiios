from setuptools import setup, find_packages

setup(
    name='lunii',
    version='0.1.1a2',
    description='A Python package for working with Lunii devices, and emulating them',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Bastien Saidi',
    author_email='saidibastien@gmail.com',
    url='https://github.com/bastien8060/lumiios',
    packages=['lunii'],
    package_data={'lunii': ['data/titles.json']},
    install_requires=[
        # List the required packages here
        'xxtea >= 2.0.0',
        'climage >= 0.1.2',
        'Pillow >= 7.2.0',
        'python-vlc >= 2.2.6100',
        'appdirs',
        'requests',
    ],
    entry_points={
        'console_scripts': ['lunii-cli=lumiios.cli:main']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Education',
        'Topic :: Multimedia',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Emulators'
    ],
)