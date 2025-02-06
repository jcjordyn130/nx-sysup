import struct
import os
import subprocess
import tempfile
import argparse
import pathlib
import shutil

sysver_format = "BBBBBBBBH20s40s24s128s" # Thank you ChatGPT... this is the format of the system version file: https://switchbrew.org/wiki/System_Version_Title
sysver_titleid = "0100000000000809" # TitleID for the system version data archive
debug = False # Make each function log a lot more

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
			if debug:
				print(f"Skipping non-Nintendy archive {cnt}!")

			continue

		print(f"Processing NCA {cnt}!")
		proc = subprocess.run(["hactool", "-i", os.path.join(ext_update_path, cnt)], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)

		for line in proc.stdout.splitlines():
			if line.startswith("Title ID:"):
				# Grab title ID
				titleid = line.split(" ")[-1]
				if titleid == sysver_titleid:
					return os.path.join(ext_update_path, cnt)

	return None

def extract_sysver_nca(nca):
	tempdir = tempfile.TemporaryDirectory(prefix = "NX_SYSUP-")
	if debug:
		print(f"Extracting {nca} to {tempdir.name}!")

	subprocess.run(["hactool", "-x", f"--romfsdir={tempdir.name}", nca], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
	return tempdir


def parse_update(update_path):
	print("[1/3] Finding sysver NCA...")
	sysver_nca = find_sysver_nca(update_path)
	if not sysver_nca:
		print(f"ERROR: sysver NCA was not found in extracted update at {update_path}!")
		raise SystemExit(1)

	print("[2/3] Extracting sysver NCA...")
	temp = extract_sysver_nca(sysver_nca)

	print("[3/3] Parsing sysver file...")
	sysver = parse_sysver(os.path.join(temp.name, "file"))

	print(f"System Update Version: {sysver[0]}.{sysver[1]}.{sysver[2]}")

def extract_update(path):
	# Extract update from XCI
	print(f"[1/5] Extracting update from XCI...")
	tempdir = tempfile.TemporaryDirectory(prefix = "NX_SYSUP-")
	subprocess.run(["hactool", f"--updatedir={tempdir.name}", "-t", "xci", path], stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)

	# Find the sysver NCA
	print(f"[2/5] Finding sysver NCA...")
	sysver_nca = find_sysver_nca(tempdir.name)
	if not sysver_nca:
		print(f"ERROR: sysver NCA was not found in extracted update from {path}!")
		raise SystemExit(1)

	# Extract it so we can parse the file
	print(f"[3/5] Extracting sysver NCA...")
	sysver_dir = extract_sysver_nca(sysver_nca)

	# Grab the sysver
	print(f"[4/5] Parsing sysver file...")
	sysver = parse_sysver(os.path.join(sysver_dir.name, "file"))

	# Final move
	print(f"[5/5] Moving into properly named directory...")
	shutil.move(tempdir.name, f"NX_UPDATE_{sysver[0]}.{sysver[1]}.{sysver[2]}_{path.stem}")
	print(f"Update {sysver[0]}.{sysver[1]}.{sysver[2]} from {path.stem} was successfully extracted!")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog = "NX-SYSUP")
	parser.add_argument("--debug", help = "Increases logging")
	parser.add_argument("--path-to-hactool", help = "Path to hactool", type = pathlib.Path)
	parser.add_argument("--from-xci", help = "Path to XCI to extract update from", type = pathlib.Path)
	parser.add_argument("--parse-update", help = "Path to extracted update to grab version from", type = pathlib.Path)
	args = parser.parse_args()

	# Set debug logging global if parameter is passed...
	if args.debug:
		debug = True

	# Add hactool to $PATH if given
	if args.path_to_hactool:
		if debug:
			print("hactool path given... adding to $PATH!")

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
		parse_update(args.parse_update)
	elif args.from_xci:
		extract_update(args.from_xci)
	else:
		print(f"ERROR: --from-xci OR --parse-update are required!")
		raise SystemExit(1)
