from setuptools import setup, find_packages

NAME = 'Products.NaayaNetRepository'

setup(name=NAME,
      version='1.0.6',
      description="",
      long_description=open("README.txt").read().strip(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
      ],
      keywords='',
      author='EaudeWeb',
      author_email='office@eaudeweb.ro',
      url='http://naaya.eaudeweb.ro/',
      license='MPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Naaya >= 2.13.17',
      ],
)
