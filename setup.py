from setuptools import setup, find_packages


long_desc = open('README.rst', 'rb').read().decode('utf-8')

setup(
    name='django-markdown-view',
    description='Serve .md pages as Django views.',
    long_description=long_desc,
    author='Ryan J. Sullivan',
    author_email='ryanj@ryanjsullivan.com',
    license='BSD',
    url='http://github.com/rgs258/django-markdown-view',
    packages=find_packages(),
    install_requires=[
        'django>=2.2',
        'markdown>=3.2',
    ],
    tests_require=[
        'tox',
    ],
    keywords=['django', 'markdown', 'markdown view', 'md'],
    include_package_data=True,
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django :: 2',
        'Framework :: Django :: 3',
        'Framework :: Django :: 4',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    zip_safe=False,
)
