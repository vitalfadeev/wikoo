SET SELFPATH=%~dp0
cd %SELFPATH%
python -m cProfile -o profile.dat wikidict.py
python profile-view.py > profile.txt
profile.txt
