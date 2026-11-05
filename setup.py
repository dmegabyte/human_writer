from setuptools import setup, find_packages

setup(
    name="human_writer",
    version="0.1.0",
    description="Modular Zero-Slop Factual Review and Text Generation Engine",
    author="Ser",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pandas",
        "pyyaml"
    ],
)
