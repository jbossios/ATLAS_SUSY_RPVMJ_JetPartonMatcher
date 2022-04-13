import setuptools

with open("README.md", "r") as fh:

    long_description = fh.read()

setuptools.setup(

    name="jbossios",

    version="1.0.0",

    author="Jonathan Bossio",

    author_email="",

    description="Jet-parton matcher for the SUSY RPV MJ search",

    long_description=long_description,

    long_description_content_type="text/markdown",

    url="https://github.com/jbossios/ATLAS_SUSY_RPVMJ_JetPartonMatcher",

    packages=setuptools.find_packages(),

    classifiers=[

        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: MIT License",

        "Operating System :: OS Independent",

    ],

    python_requires='>=3.8',

)
