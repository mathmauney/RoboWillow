from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    install_requires=requirements,

    entry_points={
        'console_scripts': [
            'robowillow=robowillow.__main__:main'
        ],
    },
)
