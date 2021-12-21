# EasyTerrain v.1.0.0
_EasyTerrain simplifies terrain creation process by automatically slicing a template image with terrain assets and converting them to format ready for SpriteEditor._

## Usage
Fill supplied **template.png** with assets of your terrain, save it as **input.png** (using indexed mode with transparency or as normal PNG in RGBA mode) and run the script. Terrain files ready for conversion will be created in **output/** directory. Convert the files with supplied **SpriteEditor.exe** to create **Level.dir** and **icon.img** (rename it to **text.img** in **Worms Armageddon/DATA/Level/YourTerrain** directory).

See provided **input.png** for example how to put your assets.

Sample **gradient.img.bmp** and **icon.img.bmp** have been provided in **data/** directory to make the terrain work out of the box, but you will need to customize them manually.

Debris sprite must be transparent and use a 1px stroke outside its bounding box. Sample debris sprites have been provided in **debris samples.png**. If your debris animation exceeds the available vertical space, you can simply resize the template image.
Remember to update **data/debris.spr.spd** with width, height and frames used in your debris animation.

## Command line options
```
usage: easyterrain.py [-h] [--input INPUT] [--data DATA] [--output OUTPUT] [--transparencycolor #RRGGBB] [--noalign]

options:
  -h, --help            show this help message and exit
  --input INPUT         Path to indexed PNG file with terrain assets (default: input.png)
  --data DATA           Path to data directory with easyterrain data files (default: data)
  --output OUTPUT       Path to output directory with generated terrain files (default: output)
  --transparencycolor #RRGGBB
                        Replace color 0 in palette (used in WA as transparency) with this color (default: #FF00FF)
  --noalign             Disable aligning IMG files to dimensions divisible by 4 (default: False)
```
