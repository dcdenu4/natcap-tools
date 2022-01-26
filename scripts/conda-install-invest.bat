@ECHO OFF
:: Run the commented code first before executing this script from within
:: your invest repository
:: conda create -p .\venv-space\py397-invest python=3.9.7 -c conda-forge
:: conda activate .\env-space\py397-invest
call conda install nomkl
call conda install numpy=1.20 gdal=3.3.1 build twine
call python ./scripts/convert-requirements-to-conda-yml.py requirements.txt requirements-dev.txt requirements-gui.txt > requirements-all.yml
call conda env update --file requirements-all.yml

PAUSE
