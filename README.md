# Quantifying urbanization

Urbanization is a foundational aspect of understanding the human condition, and has been a focus of economic, social, and development study for many years. This code repository is meant to centralize many of the urban analytics performed by the [World Bank's Global Operational Support Team (GOST)](https://worldbank.github.io/GOST) in support of World Bank Group operations. There are numerous code examples in the [notebooks](https://github.com/worldbank/GOST_Urban/tree/main/notebooks) folder including both tutorials and records of project implementations.

This repo includes a [GitHub Pages](https://worldbank.github.io/GOSTurban/README.html) and a [Wiki](https://github.com/worldbank/GOST_Urban/wiki) for the documentation.

## Installation

### From PyPI

**GOSTurban** is available on [PyPI](https://pypi.org/project/GOSTurban/) and can installed using `pip`:

```shell
pip install GOSTurban
```

### From Source

1. Clone or download this repository to your local machine. Then, navigate to the root directory of the repository:

    ```shell
    git clone https://github.com/worldbank/GOSTurban.git
    cd GOSTurbang
    ```

2. Create a virtual environment (optional but recommended):

    ```shell
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the package with dependencies:

    ```shell
    pip install .
    ```

    Install the package **in editable** mode with dependencies:

    ```shell
    pip install -e .
    ```

    The `-e` flag stands for "editable," meaning changes to the source code will immediately affect the installed package.

## License

This project is licensed under the [**MIT**](https://opensource.org/license/mit) - see the [LICENSE](LICENSE) file for details.
