from setuptools import setup, find_packages

setup(name='naaya.envirowindows',
    version='1.1.11',
    author='Eau de Web',
    author_email='office@eaudeweb.ro',
    url='http://naaya.eaudeweb.ro',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Naaya',
    ]
)
