# Steam Workshop Automatic

![Swautomatic](https://img.shields.io/badge/Swautomatic-v1.0-f08080?style=flat-square)
![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=ffdd54)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=?flat-square&&logo=mongodb&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat-square&logo=flask&logoColor=white)
![License](https://img.shields.io/github/license/antydemidov/swautomatic?style=flat-square)

![Sponsors](https://img.shields.io/github/sponsors/antydemidov?style=flat-square)
![Last commit](https://img.shields.io/github/last-commit/antydemidov/swautomatic?style=flat-square)
![Issues](https://img.shields.io/github/issues/antydemidov/swautomatic?style=flat-square)
![Downloads](https://img.shields.io/github/downloads/antydemidov/swautomatic/total?style=flat-square)

## What is it?

Python & Flask web-app that automatically updates mods for the game.

Current version: `v1.0`
*It may have a lot of errors. So please be careful and patient.*

## Main features

1. Collecting you favourite assets from Steam Workshop;
2. Checking the updates;
3. Downloading assets and mods;
4. Filtering assets by tags;

## Funding

No one financed me except for my parents. Maybe you would also like to do it?

## Roadmap

### `v1.0`

- [x] Detect files from zip files.
- [x] Retrieving a list of favorite assets from Steam Workshop.
- [x] Updating the asset information in the database.
- [x] Downloading previews and asset files.
- [x] Removing assets.
- [x] Filtering assets by tags and status (installed, requires update, or not installed).
- [x] Full database update.
- [x] Updating assets.
- [x] Full database reset, including assets and previews.

### `v2.0`

- [ ] [#13](https://github.com/antydemidov/swautomatic/issues/13) Check requirements of assets and mods.
- [ ] [#17](https://github.com/antydemidov/swautomatic/issues/17) Add authorization via Steam.
- [ ] [#34](https://github.com/antydemidov/swautomatic/issues/34) Supporting another games.

Something else?.. You can check the [issues](https://github.com/antydemidov/swautomatic/issues).

## Requirements

- **Python 3.11**
- beautifulsoup4 - 4.11.1
- python-decouple - 3.6
- Flask - 2.2.3
- Flask-WTF - 1.0.1
- Pillow - 9.4.0
- pymongo - 4.3.3
- python-decouple - 3.8
- python-dotenv - 0.21.0
- requests - 2.28.1

## Installation [↩](docs/installation.md)

## Documentation [↩](docs/index.md)

## License [↩](LICENSE)

[BSD 3-Clause License](https://opensource.org/license/bsd-3-clause/)
