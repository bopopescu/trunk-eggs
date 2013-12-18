from setuptools import setup, find_packages

setup(name='naaya.content.meeting',
      version='1.2.51',
      author='Eau de Web',
      author_email='office@eaudeweb.ro',
      url='http://naaya.eaudeweb.ro',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Naaya >= 3.3.24',
          'BeautifulSoup >= 3.0.7a',
          'scrubber >= 1.4.2',
          'naaya-survey >= 1.2.21',
          'html2text',
      ],
)

