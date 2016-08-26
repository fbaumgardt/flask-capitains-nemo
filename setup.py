from setuptools import setup, find_packages

version = "1.0.0b2"

setup(
    name='flask_nemo',
    version=version,
    packages=find_packages(exclude=["examples", "tests"]),
    url='https://github.com/capitains/flask-capitains-nemo',
    license='GNU GPL',
    author='Thibault Clerice',
    author_email='leponteineptique@gmail.com',
    description='Flask Extension to browse CTS Repository',
    test_suite="tests",
    install_requires=[
        "MyCapytain>=1.0.1",
        "requests_cache>=0.4.9",
        "Flask>=0.10.1",
        "requests>=2.10.0"
    ],
    tests_require=[
        "mock==1.0.1",
        "capitains_nautilus>=0.0.4"
    ],
    entry_points={
        'console_scripts': ['capitains-nemo=flask_nemo:cmd'],
    },
    include_package_data=True,
    zip_safe=False
)
