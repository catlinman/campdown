
# Doesn't seem to be working at the moment.
from setuptools import setup

setup(
    name='campdown',
    version='1.0',
    author='Catlinman',
    author_email='contact@catlinman.com',
    description=('Bandcamp track and album downloader'),
    long_description=open('README.md').read(),
    license='MIT',
    keywords=['bandcamp', 'downloader', 'utility'],
    url='https://github.com/catlinman/campdown/',
    packages=["campdown"],
    install_requires=['requests', 'mutagen'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'campdown=campdown.__main__.main',
        ],
    },
)
