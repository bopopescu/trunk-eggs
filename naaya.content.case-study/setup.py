from setuptools import setup, find_packages

setup(name='naaya.content.case-study',
      version='0.0.2',
      author='Eau de Web',
      author_email='office@eaudeweb.ro',
      url='http://naaya.eaudeweb.ro',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Naaya',
      ],
)

