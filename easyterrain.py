import argparse
import logging
import math
import os
import pathlib
from dataclasses import dataclass

from PIL import Image, ImageColor


@dataclass
class InputRegion:
	name: str
	type: str
	objtype: str
	x: int
	y: int
	width: int
	height: int
	crop: bool
	addtoindex: bool
	useinf: bool
	usespd: bool

	def __post_init__(self):
		self.fullname = f'{self.name}.{self.type}'


def round_up(num, div):
	return math.ceil(num/div) * div

def align_bbox(bbox):
	old_width = bbox[2] - bbox[0]
	old_height = bbox[3] - bbox[1]
	new_width = round_up(old_width, 4)
	new_height = round_up(old_height, 4)
	shift_width = round((new_width - old_width)/2)
	shift_height = round((new_height - old_height)/2)
	new_bbox = (bbox[0] - shift_width, bbox[1]-shift_height, bbox[0]-shift_width+new_width, bbox[1]-shift_height+new_height)
	return new_bbox

def convert_region(outputdir, region, image, transparent_index, transparency_color, align):
	logging.debug(f'Converting region: {region}')

	im = image.crop((region.x, region.y, region.x + region.width, region.y + region.height))

	if region.crop:
		imcopy = im.copy().convert('RGBA')
		bbox = imcopy.getbbox()
		if bbox is None:
			logging.debug('\t Empty region')
			return None
		if region.type == 'img' and align:
			bbox = align_bbox(bbox)
		im = im.crop(bbox)
		logging.debug(f'\tCropped to: {im.width}x{im.height}')

	if transparent_index != 0:
		# move transparent color to first position in palette and replace it with magenta
		palette = im.getpalette()
		palette = list(transparency_color) + palette[:-3]
		for i in range(transparent_index * 3, 256 * 3):
			palette[i] = 0
		im.putpalette(palette)

		data = im.getdata()
		# replace transparent regions with color 0, shift other color data by 1
		newdata = [0 if x == transparent_index else x+1 for x in data]
		im.putdata(newdata)
	else:
		# replace transparent color with magenta
		palette = im.getpalette()
		palette[0:3] = list(transparency_color)
		im.putpalette(palette)

	if region.name == 'debris':
		im = im.crop((1,1,im.width-1, im.height-1))

	output = outputdir / f'{region.fullname}.bmp'
	im.save(output)
	return im


def convert(inputfile, outputdir, datadir, transparency_color=(255, 0, 255), align=True):
	image = Image.open(inputfile)
	if image.mode == 'RGBA':
		logging.info(f'Converting {inputfile} to indexed mode')
		image = image.quantize(colors=96, method=None, kmeans=0, palette=None, dither=Image.FLOYDSTEINBERG)
	elif image.mode == 'P':
		pass
	else:
		raise Exception(f'{image.mode} mode images are not supported. Use Indexed or RGBA mode.')

	transparent_index = image.getpixel((0, image.height -1)) # probe color id of bottom-left corner to find transparency id
	logging.debug(f'Transparent color palette index: {transparent_index}')

	regions = [
		InputRegion("text", "img", "required", 64, 64, 256, 256, False, False, False, False),
		InputRegion("soil", "img", "required", 384, 64, 256, 256, False, False, False, False),
		InputRegion("bridge-l", "img", "required", 64, 384, 128, 128, True, False, False, False),
		InputRegion("bridge", "img", "required", 256, 384, 128, 128, True, False, False, False),
		InputRegion("bridge-r", "img", "required", 448, 384, 128, 128, True, False, False, False),
		InputRegion("grass", "img", "required", 64, 576, 192, 128, True, False, False, False),
		InputRegion("back", "spr", "back", 64, 896, 1024, 1024, True, False, False, True),
		InputRegion("_back", "spr", "back", 64, 2112, 1024, 1024, True, False, False, True),
		InputRegion("back2", "spr", "optional", 64, 3328, 1024, 1024, True, False, False, True),
		InputRegion("front", "spr", "optional", 64, 4544, 1024, 1024, True, False, False, True),
		InputRegion("debris", "spr", "required", 7168, 192, 192, image.height - 256, True, False, False, True),
	]
	count_back = 2

	filelist = ['gradient.img', 'icon.img', 'index.txt'] # Level.dir.txt
	inflist = [] # index.txt

	for objtype, y in [('floor', 64), ('side', 1920), ('roof', 3776)]:
		for row in range(3):
			x = 1280
			for i in range(10):
				regions.append(InputRegion(f'{objtype}{row}{i}','img', objtype, x, y, 512, 512, True, True, True, False))
				x+= 512 + 64
			y += 512 + 64

	for region in regions:
		res = convert_region(outputdir, region, image, transparent_index, transparency_color, align)
		if not res:
			if region.objtype == 'required':
				logging.error(f'{region.fullname} is missing - this terrain may crash the game!!!')
			elif region.objtype == 'back':
				count_back -= 1
				if count_back == 0:
					logging.error(f'back.spr and _back.spr are missing - this terrain may crash the game!!!')
			continue

		filelist.append(region.fullname)

		if region.useinf:
			pathin = datadir / f'{region.objtype}.inf'
			pathout = outputdir / f'{region.name}.inf'
		elif region.usespd:
			pathin = datadir / f'{region.fullname}.spd'
			pathout = outputdir / f'{region.fullname}.spd'
		else:
			pathin, pathout = None, None

		if pathin is not None and pathin.exists():
			with open(pathin, 'r') as fin, open(pathout, 'w') as fout:
				contents = fin.read().format(width=res.width, height=res.height)
				fout.write(contents)

			if region.addtoindex:
				filelist.append(f'{region.name}.inf')
				inflist.append(pathout.stem)

	with open(outputdir / 'Level.dir.txt', 'w') as f:
		for line in filelist:
			f.write(f'{line}\n')

	with open(outputdir / 'index.txt', 'w') as f:
		for line in inflist:
			f.write(f'{line}\n')

	for name in ['gradient.img.bmp', 'icon.img.bmp', 'SpriteEditor.exe']:
		pathin = datadir / name
		pathout = outputdir / name
		if not pathout.exists():
			with open(pathin, 'rb') as fin, open(pathout, 'wb') as fout:
				fout.write(fin.read())


if __name__ == '__main__':
	logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.INFO)

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--input', help='Path to indexed PNG file with terrain assets', required=False, default='input.png')
	parser.add_argument('--data', help='Path to data directory with easyterrain data files', required=False, default='data')
	parser.add_argument('--output', help='Path to output directory with generated terrain files', required=False, default='output')
	parser.add_argument('--transparencycolor', help='Replace color 0 in palette (used in WA as transparency) with this color', required=False, default='#FF00FF', type=str)
	parser.add_argument('--noalign', help='Disable aligning IMG files to dimensions divisible by 4', required=False, default=False, action='store_true')
	args = parser.parse_args()

	inputfile = pathlib.Path(args.input)
	outputdir = pathlib.Path(args.output)
	datadir = pathlib.Path(args.data)
	transparency_color = ImageColor.getcolor(args.transparencycolor, "RGB")
	align = not args.noalign

	os.makedirs(outputdir, exist_ok=True)
	os.makedirs(datadir, exist_ok=True)

	logging.info(f'Converting {inputfile} to {outputdir} directory')
	convert(inputfile, outputdir, datadir, transparency_color, align)
	logging.info('Finished')

