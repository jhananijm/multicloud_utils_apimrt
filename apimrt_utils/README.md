## Doc Generation

sphinx-build -b singlehtml docs/source/ docs/build/html

## Building wheel package

python3 setup.py bdist_wheel

## Installing the package for different clouds

```bash


pip install apimrt[apim-aws]

pip install apimrt[apim-gcp]

pip install apimrt[apim-azure]

pip install apimrt[apim-alibaba]

pip install apimrt[apim-cc3]

