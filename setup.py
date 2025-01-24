from setuptools import setup, find_packages

setup(
    name='codemind_mvp',  # Or choose a name for your project
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'google-generativeai',
        'anthropic',
        'python-dotenv',
    ],
)