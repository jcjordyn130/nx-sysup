# nx-sysup
A System Update Extractor for the NX Platform (Nintendo Switch)

This tools can either parse a version from an extracted update via the system version NCA and can extract
updates from a given XCI.

# Why did I create this?
Simple, Nintendo sent DMCA takedown requests to the websites around the web that are hosting firmware dumps and I needed a very specific version of HOS.

So I created this tool to extract them from game dumps, esp launch titles with 1.0.0.

# Features
- [X] Parsing System Update Version from Extracted Update
- [X] Extracting Update from XCI
- [ ] Extracting Update from NSP
- [ ] Handling XCI/NSP with no update partition
- [ ] Parsing game title name/id/version from XCI/NSP

# How to Use
```
usage: NX-SYSUP [-h] [--debug DEBUG] [--path-to-hactool PATH_TO_HACTOOL]
                [--from-xci FROM_XCI] [--parse-update PARSE_UPDATE]

options:
  -h, --help            show this help message and exit
  --debug DEBUG         Increases logging
  --path-to-hactool PATH_TO_HACTOOL
                        Path to hactool
  --from-xci FROM_XCI   Path to XCI to extract update from
  --parse-update PARSE_UPDATE
                        Path to extracted update to grab version from
```
nx-sysup requires hactool to be installed and for decryption keys to be installed.

Decryption keys *must* be obtained from a personally owned console through tools that shall not be named here, or for the XCI and System Update NCAs to be decrypted already.

It works with all the games in my library, except for ToTk.

`--from-xci` and `--parse-update` are mutually exclusive as `--from-xci` implies `--parse-update`.

Extracted updates are placed in the current directory named as such: `NX_UPDATE_{major}.{minor}.{patch}_{XCI filename}`.

Support is planned for parsing the game title name, id, and version from a given XCI/NSP, but I have yet to find a way to handle that gracefully (without extracting the entire XCI/NSP) due to differences around 4.x.x-5.x.x HOS titles and the Normal/Logo partitions.

# Credits
- [@SciresM](https://github.com/SciresM) for [hactool](https://github.com/SciresM/hactool) and his work on Atmosphere and early Switch homebrew
- [Switchbrew](https://switchbrew.org/wiki/Main_Page) team for documenting the switch file formats
- ChatGPT for creating a struct.Structure to parse the system update version
