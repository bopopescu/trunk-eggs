from setuptools import setup, find_packages

setup(name='Products.NaayaContent.NyConsultation',
      version='1.1.3',
      description="NyConsultation",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGELOG.rst").read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
      ],
      author='EaudeWeb',
      author_email='office@eaudeweb.ro',
      url='http://naaya.eaudeweb.ro/',
      license='MPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Naaya',
      ],
      )
