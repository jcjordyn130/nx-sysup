import struct
import os
import subprocess
import tempfile
import argparse
import pathlib
import shutil

# Details for Nintendo system files, shouldn't change.
sysver_format = "BBBBBBBBH20s40s24s128s" # Thank you ChatGPT... this is the format of the system version file: https://switchbrew.org/wiki/System_Version_Title
sysver_titleid = "0100000000000809" # TitleID for the system version data archive
cnacp_title_format = '512s256s'  # Format for a single title
cnacp_title_langs = [
	"AmericanEnglish",
	"BritishEnglish",
	"Japanese",
	"French",
	"German",
	"LatinAmericanSpanish",
	"Spanish",
	"Italian",
	"Dutch",
	"CanadianFrench",
	"Portuguese",
	"Russian",
	"Korean",
	"TraditionalChinese",
	"SimplifiedChinese",
] # control.nacp title index to language string

debug = False # Make each function log a lot more

#### Internal Functions ####
# These functions implement each aspect of the update extraction process one step at a time
def parse_sysver(sysver_file):
	struct_len = struct.calcsize(sysver_format)
	with open(sysver_file, "rb") as file:
		while True:
			data = file.read(struct_len)
			s = struct.Struct(sysver_format).unpack_from(data)
			break

	return s[0], s[1], s[2]

def find_sysver_nca(ext_update_path):
	for cnt in os.listdir(ext_update_path):
		# We don't need CNMT files... only the actual archives with RomFSes in them...
		if not cnt.endswith(".nca") or cnt.endswith(".cnmt.nca"):
			debug_print(f"Skipping non-Nintendy archive {cnt}!")

			continue

		debug_print(f"Processing NCA {cnt}!")
		titleid = grab_nca_titleid(os.path.join(ext_update_path, cnt))
		if titleid == sysver_titleid:
			return os.path.join(ext_update_path, cnt)

	return None

def grab_nca_titleid(nca):
	proc = subprocess.run(["hactool", "-i", nca], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)

	for line in proc.stdout.splitlines():
		if line.startswith("Title ID:"):
			# Grab Title ID
			return line.split(" ")[-1]

	return None

def extract_nca_romfs(nca):
	tempdir = tempfile.TemporaryDirectory(prefix = "NX_SYSUP-")
	debug_print(f"Extracting {nca} to {tempdir.name}!")

	proc = subprocess.run(["hactool", "-x", f"--romfsdir={tempdir.name}", nca], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)

	return tempdir

def extract_xci_normallogo(xci):
	tempdir = tempfile.TemporaryDirectory(prefix = "NX_SYSUP-")
	debug_print(f"Attempting to extract LogoPartition... this may fail")

	# Attempt to extract LogoPartition <4.0.0
	proc = subprocess.run(["hactool", "-x", f"--logodir={tempdir.name}", "-t", "xci", xci], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
	if len(os.listdir(tempdir.name)) == 0:
		debug_print(f"LogoPartition extraction resulted in 0 files... trying NormalPartition!")

		# Attempt to extract NormalPartition >4.0.0
		proc = subprocess.run(["hactool", "-x", f"--normaldir={tempdir.name}", "-t", "xci", xci], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
		if len(os.listdir(tempdir.name)) == 0:
			print(f"Failure extracting NormalPartition... this should not happen??? hactool returned {proc.returncode}!")
		else:
			debug_print(f"NormalPartition extracted resulted in {len(os.listdir(tempdir.name))} files")

	return tempdir

def extract_xci_update(xci):
	tempdir = tempfile.TemporaryDirectory(prefix = "NX_SYSUP-")
	proc = subprocess.run(["hactool", f"--updatedir={tempdir.name}", "-t", "xci", xci], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
	if proc.returncode > 0:
		print(f"ERROR: hactool returned {proc.returncode} while extracting update partition!")
		raise SystemExit(1)

	if len(os.listdir(tempdir.name)) == 0:
		print(F"ERROR: 0 files were found in extracted update partition yet hactool returned 0")
		raise SystemExit(1)

	debug_print(f"UpdatePartition extracted with {len(os.listdir(tempdir.name))} files!")
	return tempdir

def grab_xci_title_metadata(xci):
	print("Extracting Normal/Logo Partition...")
	normlogo = extract_xci_normallogo(xci)

	# Find NCA... there should only be one .nca and one .cnmt.nca
	ncas = [os.path.join(normlogo.name, x) for x in os.listdir(normlogo.name) if x.endswith(".nca") and not x.endswith(".cnmt.nca")]
	debug_print(f"found {len(ncas)} NCAs from extract_xci_normallogo!")

	if len(ncas) > 1:
		print(f"ERROR: Number of NCAs in Normal/Logo partition is {len(ncas)} when it should be 1!")
		raise SystemExit(1)
	elif len(ncas) == 0:
		print(f"ERROR: No NCAs found in Normal/Logo partition??? huh???")
		raise SystemExit(1)

	# Extract control.nacp from Control NCA
	print("Extracting control.nacp...")
	control_nacp = extract_nca_romfs(ncas[0])

	# Parse control.nacp
	print("Parsing control.nacp...")
	titles = parse_control_nacp(os.path.join(control_nacp.name, "control.nacp"))
	print(f"control.nacp successfully parsed....")

	return titles

def parse_control_nacp(nacp):
	titles = {}
	size = struct.calcsize(cnacp_title_format) * 13

	with open(nacp, "rb") as file:
		for app_name, pub in struct.iter_unpack(cnacp_title_format, file.read(size)):
			if len(titles) == 13:
				# Standard only has 13 languages
				break

			# Strip null bytes
			app_name = app_name.strip(b"\x00")
			pub = pub.strip(b"\x00")

			# Decode strings or set to None if they are blank
			if not app_name:
				app_name = None
			else:
				app_name = app_name.decode()

			if not pub:
				pub = None
			else:
				pub = pub.decode()

			titles.update({cnacp_title_langs[len(titles)]: (app_name, pub)})

	return titles

def parse_name_template(template, sysver, titles):
	out = template

	# Replace system version (major.minor.patch)
	out = out.replace("[version]", f"{sysver[0]}.{sysver[1]}.{sysver[2]}")

	# Replace titles and publisher strings in format using official control.nacp language strings
	for key in titles:
		# The replaces are wrapped in if statements, as str.replace does not support None to represent a blank string.
		if titles[key][0]:
			out = out.replace(f"[{key}_title]", titles[key][0])

		if titles[key][1]:
			out = out.replace(f"[{key}_publisher]", titles[key][1])

	debug_print(f"Using {out} as an update name from template {template}!")

	return out

def debug_print(*args, **kwargs):
	if debug:
		print("DEBUG:", *args, **kwargs)


#### Main Functions ####
# These operations are called below depending on the arguments passed to the script
def main_extract_titles(xci):
	# Grab XCI title metadata
	mtd = grab_xci_title_metadata(xci)
	print(f"Titles: {mtd}")

def main_parse_update(update_path):
	print("[1/3] Finding sysver NCA...")
	sysver_nca = find_sysver_nca(update_path)
	if not sysver_nca:
		print(f"ERROR: sysver NCA was not found in extracted update at {update_path}!")
		raise SystemExit(1)

	print("[2/3] Extracting sysver NCA...")
	temp = extract_nca_romfs(sysver_nca)

	print("[3/3] Parsing sysver file...")
	sysver = parse_sysver(os.path.join(temp.name, "file"))

	print(f"System Update Version: {sysver[0]}.{sysver[1]}.{sysver[2]}")

def main_extract_update(path, name):
	# Extract update from XCI
	print(f"[1/6] Extracting update from XCI...")
	tempdir = extract_xci_update(path)

	# Find the sysver NCA
	print(f"[2/6] Finding sysver NCA...")
	sysver_nca = find_sysver_nca(tempdir.name)
	if not sysver_nca:
		print(f"ERROR: sysver NCA was not found in extracted update from {path}!")
		raise SystemExit(1)

	# Extract it so we can parse the file
	print(f"[3/6] Extracting sysver NCA...")
	sysver_dir = extract_nca_romfs(sysver_nca)

	# Grab the sysver
	print(f"[4/6] Parsing sysver file...")
	sysver = parse_sysver(os.path.join(sysver_dir.name, "file"))

	# Grab control.nacp
	print(f"[5/6] Parsing control.nacp...")
	titles = grab_xci_title_metadata(path)

	# Final move
	print(f"[6/6] Moving into properly named directory...")
	parsed_name = parse_name_template(name, sysver, titles)
	shutil.move(tempdir.name, parsed_name)
	print(f"Update {sysver[0]}.{sysver[1]}.{sysver[2]} from {path.name} was successfully extracted!")



if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog = "NX-SYSUP")
	parser.add_argument("--debug", help = "Increases logging", action = "store_true")
	parser.add_argument("--nametemplate", help = "Naming template for updates", default = "NX_UPDATE_[version]_[AmericanEnglish_title]")
	parser.add_argument("--path-to-hactool", help = "Path to hactool", type = pathlib.Path)
	parser.add_argument("--from-xci", help = "Path to XCI to extract update from", type = pathlib.Path)
	parser.add_argument("--parse-update", help = "Path to extracted update to grab version from", type = pathlib.Path)
	parser.add_argument("--parse-cnacp", help = "Path to XCI to parse control.nacp from", type = pathlib.Path)

	args = parser.parse_args()

	# Set debug logging global if parameter is passed...
	if args.debug:
		debug = True

	# Add hactool to $PATH if given
	if args.path_to_hactool:	
		debug_print("hactool path given... adding to $PATH!")

		os.environ["PATH"] += os.pathsep + str(args.path_to_hactool)

	# Check for hactool
	# Returncode based checking does not work because hactool returns code 1 when no params are given
	try:
		proc = subprocess.run(["hactool"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, text = True)
	except FileNotFoundError:
		print(f"ERROR: hactool was not found in $PATH... use --path-to-hactool")
		raise SystemExit(1)

	# Run
	if args.parse_update:
		main_parse_update(args.parse_update)
	elif args.from_xci:
		main_extract_update(args.from_xci, name = args.nametemplate)
	elif args.parse_cnacp:
		main_extract_titles(args.parse_cnacp)
	else:
		print(f"ERROR: --from-xci OR --parse-update OR --parse-cnacp are required!")
		raise SystemExit(1)
