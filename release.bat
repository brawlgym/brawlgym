rm -r dist build brawlgym.egg-info
python -m build && twine check dist/* && twine upload dist/*
rm -r dist build brawlgym.egg-info
