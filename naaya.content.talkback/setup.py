from setuptools import setup, find_packages

setup(name='naaya.content.talkback',
      version='1.4.21',
      author='Eau de Web',
      author_email='office@eaudeweb.ro',
      url='http://naaya.eaudeweb.ro',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Naaya >= 2.13.20',
          'BeautifulSoup >= 3.0.7a',
          'scrubber >= 1.4.2',
          'xlrd'
      ],
)
