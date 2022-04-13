import setuptools

with open("README.md", "r") as fh:

    long_description = fh.read()

setuptools.setup(

    name="jbossios", # Replace with your username

    version="1.0.0",

    author="Jonathan Bossio",

    author_email="",

    description="A multi-purpose jet-parton matcher for the ATLAS SUSY RPV multijet search ",

    long_description=long_description,

    long_description_content_type="text/markdown",

    url="A multi-purpose jet-parton matcher for the ATLAS SUSY RPV multijet search ",

    packages=setuptools.find_packages(),

    classifiers=[

        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: MIT License",

        "Operating System :: OS Independent",

    ],

    python_requires='>=3.8',

)
