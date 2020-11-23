from setuptools import setup, find_namespace_packages

setup(name='ws2udp',
      version='0.1.0',
      packages=find_namespace_packages(include=['ws2udp']),
      entry_points={
          'console_scripts': [
              'ws2udp = ws2udp.__main__:main'
          ]
      },
      )
