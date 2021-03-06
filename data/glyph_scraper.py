import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import re
import requests, io, zipfile
import shutil
import string
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from collections import OrderedDict
from importlib import reload
import util
reload(util)

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--download", dest="download", action="store_true")
parser.add_argument("--no_download", dest="download", action="store_false")
parser.set_defaults(download=True)

# Takes roughly 30 min to run
# Outputs .ttf font files to font_files directory, .png glyph files to font_glyphs directory

mapping = OrderedDict([
			('Thin', '100'),
			('ExtraLight', '200'),
			('Extralight', '200'),
			('Light', '300'),
			('Regular', 'regular'),
			('Reg', 'regular'),
			('Medium', '500'),
			('SemiBold', '600'),
			('Semibold', '600'),
			('ExtraBold', '800'),
			('Extrabold', '800'),
			('UltraBold', '800'),
			('Ultrabold', '800'),
			('Bold', '700'),
			('Black', '900'),
			('OSF', ''),
			('Condensed', ''),
			('Italic', 'italic'),
			('It', 'italic'),
			('Oblique', 'italic'),
		])

def get_font_name_compare(file):
		if file.startswith('static/'):
			file = file[7:]
		if file.endswith('.ttf'):
			file = file[0:-4]
		name_tokens = file.split('-')
		for w, rw in mapping.items():
			if w in name_tokens[-1]:
				name_tokens[-1] = name_tokens[-1].replace(w, rw)
				if w == 'Condensed':
					name_tokens[0] += 'Condensed'	
		name = ''.join(name_tokens).lower()
		return name

def main():

	args = parser.parse_args()

	# Load font names
	data = util.FontData
	data.load()
	font_names_full = pd.DataFrame(np.sort(data.get_all_name('all'), axis=None).astype(str))
	font_names_compare = pd.DataFrame(font_names_full.iloc[:, 0].str.lower().str.split(' ').str.join(''))
	font_names_link = pd.DataFrame(font_names_full.iloc[:, 0].str.split().str[0:-1].str.join('+'))
	font_names_link = font_names_link.drop_duplicates().reset_index(drop=True).sort_values(by=0)

	# Downloads font files (ttf files)
	gf_url = 'https://fonts.google.com/download?family='
	fontfiles_path = 'data/font_files/'

	if args.download:
		if not os.path.exists(fontfiles_path):
			os.makedirs(fontfiles_path)
		for index in font_names_link.index:
			font_name = font_names_link.iloc[index, 0]
			print('Downloading font files for font family ' + font_name)
			download_url = gf_url + font_name
			try:
				r = requests.get(download_url)
				r.raise_for_status()
				z = zipfile.ZipFile(io.BytesIO(r.content))
				for file in z.namelist():
					name = get_font_name_compare(file)
					# Keep only font files whose font names are in dataset
					if name in font_names_compare.values:
						z.extract(file, fontfiles_path)
			except requests.exceptions.HTTPError as err:
				print(err)

		# Move static folder font files to top level of font files directory
		staticfiles_path = fontfiles_path + 'static/'
		if os.path.exists(staticfiles_path):
			for file in sorted(os.listdir(staticfiles_path)):
				shutil.move(staticfiles_path + file, fontfiles_path)
			os.rmdir(staticfiles_path)

		# Sanity check all 1883 fonts were scraped
		font_files_downloaded = pd.DataFrame([get_font_name_compare(f) for f in os.listdir(fontfiles_path) if not f.startswith('.')])
		n_missing_fonts = len(font_names_compare[~font_names_compare.iloc[:, 0].isin(font_files_downloaded.iloc[:, 0])])
		print(str(n_missing_fonts) + ' fonts files missing')

	# Extract per glyph png files from font files
	point_size = 10
	fig_size = (128/600, 128/600)

	fontglyphs_path = 'data/font_glyphs/'
	if not os.path.exists(fontglyphs_path):
		os.makedirs(fontglyphs_path)

	fontfiles_dir = os.fsencode(fontfiles_path)
	files_list = [os.fsdecode(f) for f in sorted(os.listdir(fontfiles_path)) if not os.fsdecode(f).startswith('.')]
	
	# seen_karma = False
	for filename in files_list:
		# if filename == "Karma-Light.ttf":
			# seen_karma = True
		# if not seen_karma:
			# continue
		print('Extracting per glyph png files from ' + filename)

		# Using matplotlib
		font_path = fontglyphs_path + filename[0:-4] + '/'
		if not os.path.exists(font_path):
			os.makedirs(font_path)

		fontfile_path = fontfiles_path + filename
		prop = font_manager.FontProperties(fname=fontfile_path)
		for char in string.ascii_letters:
			fig = plt.figure(figsize=fig_size, dpi=600)
			plt.figtext(0.5, 0.5, char, ha='center', va='center', fontproperties=prop, fontsize=point_size)
			image_path = font_path + str(ord(char)) + ".png"
			plt.savefig(image_path, dpi=600)
			plt.close(fig)

if __name__ == "__main__":
	main()
