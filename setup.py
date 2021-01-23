import setuptools

setuptools.setup(
    name="pars3",
    version="0.1",
    description="Parse s3 datas",
    url="https://github.com/SolalVall/pars3",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["boto3>=1.16.56", "click>=7.1.2", "prettytable>=2.0.0"],
    python_requires=">=3.6",
    entry_points="""
        [console_scripts]
        pars3=pars3.scripts.cli:main
    """,
)
