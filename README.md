# nx-sysup
A System Update Extractor for the NX Platform (Nintendo Switch)

This tools can parse version information from an extracted update via the system version NCA and can extract
updates from a given XCI.

# Why did I create this?
Simple, Nintendo sent DMCA takedown requests to the websites around the web that are hosting firmware dumps and I needed a very specific version of HOS.

So I created this tool to extract them from game dumps, esp launch titles with full sets of 1.0.0 NCAs.

# Features
- [X] Parsing System Update Version from Extracted Update
- [X] Extracting Update from XCI
- [X] Handling XCI with no update partition
- [X] Parsing game title name/id/version from XCI

# How to Use
```
usage: NX-SYSUP [-h] [--debug] [--nametemplate NAMETEMPLATE] [--path-to-hactool PATH_TO_HACTOOL] [--from-xci FROM_XCI] [--parse-update PARSE_UPDATE] [--parse-cnacp PARSE_CNACP]

options:
  -h, --help            show this help message and exit
  --debug               Increases logging
  --nametemplate NAMETEMPLATE
                        Naming template for updates
  --path-to-hactool PATH_TO_HACTOOL
                        Path to hactool
  --from-xci FROM_XCI   Path to XCI to extract update from
  --parse-update PARSE_UPDATE
                        Path to extracted update to grab version from
  --parse-cnacp PARSE_CNACP
                        Path to XCI to parse control.nacp from
```
nx-sysup requires hactool to be installed and for decryption keys to be installed.

Decryption keys *must* be obtained from a personally owned console through tools that shall not be named here, or for the XCI to be decrypted already.

It works with all the games in my library, except for ToTk.

`--from-xci`, `--parse-update`, and `--parse-cnacp` are mutually exclusive.

# Update Naming Template
The default naming template is `NX_UPDATE_[version]_[AmericanEnglish_title]` and is where updates are extracted to.

Here are the available keys:
- `[version]`: Replaced with the major.minor.patch tuple, example: `[version]` = 19.0.1
- `[language_title]`: Replaced with the title for the given language, example: `[AmericanEnglish_title]` = Cave Story+
- `[language_pub]`: Replaced with the publisher for a given title, example: `[AmericanEnglish_pub]` = Nicalis, Inc.

If a key is unavailable, it will NOT be replaced with any placeholder.

Here are the available languages for name replacement, however, on a lot of titles most of them are undefined. 
`AmericanEnglish` is the only language that is guaranteed by the standard:
- AmericanEnglish
- BritishEnglish
- Japanese
- French
- German
- LatinAmericanSpanish
- Spanish
- Italian
- Dutch
- CanadianFrench
- Portuguese
- Russian
- Korean
- TraditionalChinese
- SimplifiedChinese

# Credits
- [@SciresM](https://github.com/SciresM) for [hactool](https://github.com/SciresM/hactool) and his work on Atmosphere and early Switch homebrew
- [Switchbrew](https://switchbrew.org/wiki/Main_Page) team for documenting the switch file formats
- ChatGPT for creating a struct.Structure to parse the system update version
