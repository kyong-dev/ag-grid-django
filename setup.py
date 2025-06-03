from setuptools import setup, find_packages

setup(
    name='ag-grid-django',
    version='0.0.7.2',
    description='A Django app that integrates AG Grid for advanced data grid functionalities',
    author='kyong',
    author_email='kyong.dev@gmail.com',
    url='https://github.com/kyong-dev/ag-grid-django',
    # install_requires=['tqdm', 'pandas', 'scikit-learn',],
    packages=find_packages(exclude=[]),
    keywords=['ag-grid', 'django', 'ag-grid django', 'aggrid', 'aggrid django'],
    package_data={
        'ag_grid': ['contrib/*', 'contrib/**/*'],  # contrib 폴더와 모든 하위 항목 포함
    },
    python_requires='>=3.10',
    zip_safe=False,
    install_requires=[
        'openpyxl>=3.1.5',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)

