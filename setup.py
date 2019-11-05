from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='robowillow',
    version='0.0',
    description='',
    author='',
    author_email='foomail@foo.com',
    packages=['robowillow'],  #same as name
    install_requires=requirements,
    data_files=[('utils/data', ['forms.txt', 'pokemon.txt', 'pokemonwithspaces.txt'])],

    entry_points={
        'console_scripts': [
            'robowillow=robowillow.launcher:main',
            'robowillow-bot=robowillow.__main__:main']
    },
)
