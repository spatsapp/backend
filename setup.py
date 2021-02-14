import setuptools

with open("README.md", "r", encoding="utf-8") as fp:
	long_description = fp.read()

setuptools.setup(
	name='spats_backend',
	version='0.5.0'
	author='Sean Slater',
	author_email='sean@whatno.io',
	description='SPATS Personal Asset Tracking Software'
	long_description=long_description
	long_description_content_type="text/markdown",
	url="https://git.whatno.io/spslater/spats_backend"
	license='Anti-Capitalist Software License'
	packages=setuptools.find_packages(),
	classifiers=[
		'Development Status :: 4 - Beta',
		'Programming Language :: Python :: 3',
		'Operating System :: OS Independent',
		'License :: Other/Proprietary License',
	]
	python_requires='>=3.9'
)
