from setuptools import setup

setup(
    name='wikirefs',
    version='0.1',
    description='Utility to extract refs from revisions based on revids',
    url='https://github.com/kjschiroo/wikirefs',

    author='Kevin Schiroo',
    author_email='kjschiroo@gmail.com',
    license='MIT',

    packages=['wikirefs'],
    install_requires=['mwapi', 'mwparserfromhell', 'requests']
)
