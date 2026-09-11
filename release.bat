rm -r dist brawlgym.egg-info
python -m && twine check dist/* && twine upload dist/*
rm -r dist brawlgym.egg-info
