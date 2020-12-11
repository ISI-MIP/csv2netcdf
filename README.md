Converting CSV to NetCDF
========================

Script for converting CSV files to NetCDF in ISIMIP3b Marine Ecosystems and Fishery sector.

Prerequisites
-------------

The application is tested on DKRZ login nodes with Python module `python/3.5.2`.

Usage
-----

- adapt `BASE_DIR` in `convert.sh` to point to your data folder.
- use `-f` option to only process the first file found for testing purposes.
- currently the `contacts.json` file has to be obtained from `/pf/b/b324025/scripts_ISIMIP3b/model_fixes/marine-fishery_regional/csv2nc/contacts.json` but might be added to the repository at some point.
