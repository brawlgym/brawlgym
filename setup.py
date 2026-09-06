from setuptools import setup, find_packages


__version__ = None  # This will get replaced when reading version.py
exec(open('brawlgym/version.py').read())


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
    url='https://github.com/chrisrca/brawlgym',
    install_requires=[
        'numpy>=1.19',
        'py7zr>=0.20',
        'pycaw>=20220416',
    ],
    python_requires='>=3.9',
    license='Apache 2.0',
    license_file='LICENSE',
    keywords=['brawlhalla', 'gym', 'reinforcement-learning'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
    ],
    package_data={
        'brawlgym': [
            'plugin/*'
        ]
    }
)
