# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('../..'))  

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Automated User Story and Acceptance Criteria Creation Platform'
copyright = '2026, Mahek Asif Mulla'
author = 'Mahek Asif Mulla'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',       # pulls docstrings from your code
    'sphinx.ext.napoleon',      # supports Google/NumPy style docstrings
    'sphinx.ext.viewcode',      # adds "view source" links
    'sphinx.ext.autosummary',   # generates summary tables
]

autosummary_generate = True

# Optional but helpful: mock imports if some modules need heavy/external
# dependencies (e.g. API keys, DB connections) that shouldn't run at doc-build time
autodoc_mock_imports = []

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']