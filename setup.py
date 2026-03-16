import os
from setuptools import setup

here = os.path.dirname(os.path.abspath(__file__))
pymcc_path = os.path.join(here, "pymcc")

setup(
    dependency_links=[f"file://{pymcc_path}#egg=pymcc_lidar"],
    install_requires=[f"pymcc_lidar @ file://{pymcc_path}"],
)
