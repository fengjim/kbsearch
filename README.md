# kbsearch
KB Search

# Linux Install (Ubuntu 16.04)
1. Install Python
2. Install pip
3. Install mechanize
4. Install selenium
5. Install yaml
  a. sudo pip install pyyaml

6. Install phantomjs
  * download: http://phantomjs.org/download.html
  * install libfontconfig
    sudo apt-get install libfontconfig
  * set PATH TO make 'phantomjs' available for selenium

# Configuration
  config.yaml is a configuration template. Update the items accordingly.

# Execute the script
    python searchkb.py [path_to_config_file]
  By default, it assumes config.yaml is in the same directory as the script,
  and the phantomjs is available through PATH, otherwise specify it in configuration
  file accordingly.
