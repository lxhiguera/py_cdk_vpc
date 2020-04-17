import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="py_cdk_vpc",
    version="0.0.1",

    description="Component for AWS CDK to Create VPC",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Luis Higuera",
    author_email="lxhiguera@gmail.com",

 #   package_dir={"": "py_cdk_vpc"},
    packages=setuptools.find_packages(),

    install_requires=[
        "aws-cdk.core==1.32.2",
        "aws-cdk.aws_iam==1.32.2",
        "aws-cdk.aws_ec2==1.32.2",
        "ipaddress==1.0.23"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
