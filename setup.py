from distutils.core import setup

setup(name='at-hackerspace',
      author='Tomek Dubrownik',
      author_email='<t.dubrownik@gmail.com>',
      maintainer='Thomas Levine',
      maintainer_email='_@thomaslevine.com',
      description='Determine who\'s in the hackerspace based on DHCP leases.',
      url='https://github.com/tlevine/at',
      packages=['at'],
      install_requires = [
          'Flask>=0.10.1',
          'Werkzeug>=0.9.6',
          'wsgiref>=0.1.2',
          'pcapy>=0.10.8',
          'pesto>=25',
          'iscpy>=1.05',
      ],
      scripts = [
          'at-hackerspace',
      ],
      tests_require = ['nose'],
      version='0.0.3',
      license='AGPL',
      classifiers=[
          'Programming Language :: Python :: 2.7',
      ],
)
