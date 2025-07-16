#!/usr/bin/env python3
"""
Colab to Sphinx Converter - Optimized for GitHub Codespaces
Converts Colab notebook HTML and TOC to Sphinx RST format
"""

import os
import subprocess
import tempfile
from bs4 import BeautifulSoup
import re

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import sphinx
        from bs4 import BeautifulSoup
        print("✓ Required Python packages found")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Run: pip install sphinx sphinx-rtd-theme beautifulsoup4")
        return False
    
    # Check for pandoc (optional)
    try:
        subprocess.run(['pandoc', '--version'], 
                      capture_output=True, check=True)
        print("✓ Pandoc found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Pandoc not found (optional for better conversion)")
        print("Install with: sudo apt install pandoc")
        return True

def create_sphinx_project(project_name, project_path):
    """Create a basic Sphinx project structure"""
    os.makedirs(project_path, exist_ok=True)
    
    # Create conf.py
    conf_content = f'''
# Configuration file for the Sphinx documentation builder.

project = '{project_name}'
copyright = '2025'
author = 'Author'
release = '1.0'

# Add any Sphinx extension module names here
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages'  # For GitHub Pages deployment
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options for better sidebar TOC
html_theme_options = {{
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'display_version': True,
    'logo_only': False,
}}

# Enable section numbering
html_show_sourcelink = False
html_show_sphinx = False
'''
    
    with open(os.path.join(project_path, 'conf.py'), 'w') as f:
        f.write(conf_content)
    
    # Create index.rst
    index_content = f'''
{project_name}
{'=' * len(project_name)}

Welcome to the documentation for {project_name}.

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   :numbered:

   notebook_content

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''
    
    with open(os.path.join(project_path, 'index.rst'), 'w') as f:
        f.write(index_content)
    
    # Create necessary directories
    os.makedirs(os.path.join(project_path, '_static'), exist_ok=True)
    os.makedirs(os.path.join(project_path, '_templates'), exist_ok=True)
    
    print(f"✓ Sphinx project structure created in {project_path}")

def html_to_rst(html_content):
    """Convert HTML content to RST format"""
    soup = BeautifulSoup(html_content, 'html.parser')
    rst_content = []
    
    # Process different HTML elements
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'ul', 'ol', 'div']):
        if element.name.startswith('h'):
            # Convert headings
            level = int(element.name[1])
            text = element.get_text().strip()
            
            if not text:  # Skip empty headings
                continue
                
            # RST heading markers (in order of preference)
            markers = ['=', '-', '^', '"', "'", '`', '+']
            marker = markers[min(level-1, len(markers)-1)]
            
            rst_content.append('')
            rst_content.append(text)
            rst_content.append(marker * len(text))
            rst_content.append('')
            
        elif element.name == 'p':
            text = element.get_text().strip()
            if text:
                rst_content.append(text)
                rst_content.append('')
            
        elif element.name == 'pre':
            # Code blocks
            code_text = element.get_text()
            if code_text.strip():
                rst_content.append('.. code-block:: python')
                rst_content.append('')
                for line in code_text.split('\n'):
                    rst_content.append('   ' + line)
                rst_content.append('')
            
        elif element.name in ['ul', 'ol']:
            # Lists
            for i, li in enumerate(element.find_all('li', recursive=False)):
                li_text = li.get_text().strip()
                if li_text:
                    if element.name == 'ul':
                        rst_content.append(f'* {li_text}')
                    else:
                        rst_content.append(f'{i+1}. {li_text}')
            rst_content.append('')
        
        elif element.name == 'div' and 'output' in element.get('class', []):
            # Handle code output
            output_text = element.get_text().strip()
            if output_text:
                rst_content.append('.. code-block:: text')
                rst_content.append('')
                for line in output_text.split('\n'):
                    rst_content.append('   ' + line)
                rst_content.append('')
    
    return '\n'.join(rst_content)

def extract_toc_structure(html_content):
    """Extract heading structure to create internal links"""
    soup = BeautifulSoup(html_content, 'html.parser')
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    toc_structure = []
    for heading in headings:
        level = int(heading.name[1])
        text = heading.get_text().strip()
        if text:
            # Create anchor-friendly ID
            anchor = re.sub(r'[^\w\s-]', '', text.lower()).replace(' ', '-')
            toc_structure.append((level, text, anchor))
    
    return toc_structure

def convert_with_pandoc(html_content, output_rst_path):
    """Use Pandoc for HTML to RST conversion (if available)"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
        temp_html.write(html_content)
        temp_html_path = temp_html.name
    
    try:
        result = subprocess.run([
            'pandoc', 
            temp_html_path, 
            '-f', 'html', 
            '-t', 'rst', 
            '-o', output_rst_path,
            '--wrap=none'  # Don't wrap long lines
        ], check=True, capture_output=True, text=True)
        print("✓ Pandoc conversion successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ Pandoc conversion failed: {e}")
        return False
    except FileNotFoundError:
        print("⚠ Pandoc not found, using built-in converter")
        return False
    finally:
        os.unlink(temp_html_path)

def convert_colab_to_sphinx(notebook_html, toc_html, output_dir, project_name="Notebook Documentation"):
    """Main function to convert Colab notebook to Sphinx RST"""
    
    print(f"Converting Colab notebook to Sphinx project: {project_name}")
    
    # Create Sphinx project
    create_sphinx_project(project_name, output_dir)
    
    # Try Pandoc first, fall back to built-in converter
    rst_file_path = os.path.join(output_dir, 'notebook_content.rst')
    
    if not convert_with_pandoc(notebook_html, rst_file_path):
        # Use built-in converter
        print("Using built-in HTML to RST converter")
        notebook_rst = html_to_rst(notebook_html)
        
        # Create the content with proper RST structure
        full_rst_content = f'''
Notebook Content
================

{notebook_rst}
'''
        
        # Write the RST file
        with open(rst_file_path, 'w', encoding='utf-8') as f:
            f.write(full_rst_content)
    
    print(f"✓ Sphinx project created in: {output_dir}")
    return output_dir

def build_documentation(project_path):
    """Build the Sphinx documentation"""
    print("Building HTML documentation...")
    
    try:
        result = subprocess.run([
            'sphinx-build', 
            '-b', 'html', 
            project_path, 
            os.path.join(project_path, '_build', 'html')
        ], check=True, capture_output=True, text=True)
        
        print("✓ Documentation built successfully!")
        html_path = os.path.join(project_path, '_build', 'html', 'index.html')
        print(f"Open: {html_path}")
        
        # In Codespaces, suggest port forwarding
        print("\n📝 In GitHub Codespaces:")
        print("1. Use the built-in Simple Browser extension")
        print("2. Or set up a simple HTTP server:")
        print(f"   cd {os.path.join(project_path, '_build', 'html')}")
        print("   python -m http.server 8000")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print("Error output:", e.stderr)
        return False

def main():
    """Main function with example usage"""
    print("Colab to Sphinx Converter for GitHub Codespaces")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Example usage
    sample_notebook_html = """
    <h1>My Data Science Notebook</h1>
    <p>This is an example notebook converted from Colab.</p>
    
    <h2>Data Loading</h2>
    <pre>
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')
print(df.head())
    </pre>
    
    <h2>Data Analysis</h2>
    <p>Here we perform some basic analysis.</p>
    
    <h3>Summary Statistics</h3>
    <pre>
print(df.describe())
    </pre>
    """
    
    sample_toc_html = """
    <ul>
        <li><a href="#data-loading">Data Loading</a></li>
        <li><a href="#data-analysis">Data Analysis</a>
            <ul>
                <li><a href="#summary-statistics">Summary Statistics</a></li>
            </ul>
        </li>
    </ul>
    """
    
    # Convert to Sphinx
    output_dir = "./sphinx_notebook"
    project_path = convert_colab_to_sphinx(
        sample_notebook_html, 
        sample_toc_html, 
        output_dir, 
        "My Data Science Notebook"
    )
    
    # Build documentation
    if build_documentation(project_path):
        print("\n🎉 Success! Your notebook is now a Sphinx documentation site.")
        print("The TOC will appear in the left sidebar when you open the HTML.")

if __name__ == "__main__":
    main()
