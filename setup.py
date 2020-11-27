from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='ws2udp',
      version='0.1.4',
      author='Bruno Gola',
      author_email='me@bgo.la',
      description='A WebSocket to UDP proxy',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/bgola/ws2udp",
      packages=find_namespace_packages(include=['ws2udp']),
	  classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Operating System :: OS Independent",
		  "Framework :: AsyncIO",
      ],
	  install_requires=['websockets'],
      keywords='websockets udp osc opensoundcontrol',
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
              'ws2udp = ws2udp.__main__:main'
          ]
      },
      )
