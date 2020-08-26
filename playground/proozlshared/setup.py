import setuptools

setuptools.setup(
    name='proozlshared',
    version='0.1.0',
    description='Libraries shared across proozl functions',
    author='Ezra Ablaza',
    author_email='ezra.ablaza.inbox@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'nltk', 
        'requests', 
        'feedparser'],
    classifiers=[
        'Programming Language :: Python :: 3'
    ]
)