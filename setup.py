from setuptools import setup, find_packages


long_desc = open('README.rst', 'rb').read().decode('utf-8') + '\n\n' + \
            open('AUTHORS.rst', 'rb').read().decode('utf-8') + '\n\n' + \
            open('CHANGELOG.rst', 'rb').read().decode('utf-8')

setup(
    name='django-markdown-view',
    version='0.0.3',
    description='Serve .md pages as Django views.',
    long_description=long_desc,
    author='Ryan J. Sullivan',
    author_email='ryanj@ryanjsullivan.com',
    license='BSD',
    url='http://github.com/rgs258/django-markdown-view',
    packages=find_packages(),
    install_requires=[
        'django>=2.2,<4.0',
        'markdown>=3.2,<3.3',
    ],
    tests_require=[
        'tox',
    ],
    keywords=['django', 'markdown', 'markdown view', 'md'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 2.2',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    zip_safe=False,
)
