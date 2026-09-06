rm -r dist brawlgym.egg-info
python setup.py sdist && twine upload dist/*
rm -r dist brawlgym.egg-info
