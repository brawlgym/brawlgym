from setuptools import setup, find_packages
from setuptools.dist import Distribution


__version__ = None  # This will get replaced when reading version.py
exec(open('brawlgym/version.py').read())


class BinaryDistribution(Distribution):
    """The bundled engine is a CPython 3.11 win_amd64 extension, so the wheel is not pure."""
    def has_ext_modules(self):
        return True


with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()


setup(
    name='brawlgym',
    packages=find_packages(),
    version=__version__,
    description='A python API that can be used to treat the game Brawlhalla as an OpenAI Gym-like environment for '
                'Reinforcement Learning projects.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='chrisrca',
    url='https://github.com/brawlgym/brawlgym',
    install_requires=[
        'numpy>=1.19',
        'py7zr>=0.20',
        'pycaw>=20220416',
    ],
    python_requires='==3.11.*',
    distclass=BinaryDistribution,
    license='Apache 2.0',
    license_file='LICENSE',
    keywords=['brawlhalla', 'gym', 'reinforcement-learning'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows',
    ],
    package_data={
        'brawlgym': [
            'plugin/*',
        ],
        'brawlgym.core': [
            '*.pyd',
        ]
    }
)
