# Texture editing

There are two sets of G1T (texture-related) files for the game:

1. normal G1T files, most of these can be found in: `Misc\File_Formats\G1T`. Other locations: `nx\action\texture`, `nx\ui\200_title`, `nx\ui\400_abbey`, `nx\ui\font`.
2. G1T binary files, which is a binary container for various G1T files in one file. These can be found in: `Misc\File_Formats\G1T_BIN`.

Patches, DLCs may either overwrite some of these files or add new ones, so that's something to keep in mind before changing one of these (always check if there's not a newer one from a patch). This is not extensively documented here. See the *FE3H Files.xlsx* file for more information about that.

## Alternative tool

Besides the scripts here, you can simply use [G1Tool](https://github.com/three-houses-research-team/G1Tool) to manage all the G1T files as well. However, that GUI app, while easy to use, gets extremely cumbersome the moment you want to either batch extract ot batch replace a lot of files at once. It's very useful for inspection (check if file is valid, mipmap info, how the images look/what's inside, etc.) and for one-on-one replacements, but for doing numerous texture replacements, it gets tedious and time-consuming fast.

Be aware that the PNGs extracted with this *G1Tool* app do not have straight alpha, so it's best if you use a little correction on them after extraction (if the image has an alpha channel), such as this one for a file (otherwise you'll have transparency issues when converting back to DDS):

```
magick image.png png32:image.png
```

## Extracting G1T files

Whether it's a regular G1T or a binary one, the script to extract or dump their image files is the same:

```
python g1t_extract.py <filename.g1t>
```

If you'd like, you can extract it to a different output folder (otherwise the new directory becomes the filename in the same location as the G1T file):

```
python g1t_extract.py -o <extracted_dir> <filename.g1t>
```

You will get files like `0000.dds`, `0001.dds` and so on (it depends on the number of textures the file has). For the binary (or container) one, the new directory will have numerous g1t entries and then those will also get extracted in their respective subfolders.

Also, if you have **ImageMagick** or **Texconv** installed and available in your *PATH* environment variable, then the script will also use one of those to convert the DDS to PNG automatically. Alternatively, you can do this yourself or just keep working with the DDS, and you may use other tools as well, such as [compressonator](https://github.com/GPUOpen-Tools/compressonator) or [Cuttlefish](https://github.com/akb825/Cuttlefish). Then you can edit/work with either the DDS or PNG, as you prefer.

If the script did not convert the DDS files to PNG, or you wish to do it manually yourself, you can use this command (this requires *ImageMagick*):

```
magick mogrify -format png -quality 100 *.dds
```

Use this over *texconv*, because this also embeds the sRGB ICC profile in the PNG (or similar), so that image viewers will also display the PNG properly.

## Editing and converting

Now that you have the images, you can edit them with whatever image editor you fancy using (though for DDS, you need DDS support).

The images in FE3H don't really have mipmaps, so they should not be generated when converting the files back. Still, it might worth a try/experiment to generate a new file or new files with all mipmap levels enabled and see what happens. If the game engine does not request mip levels, then they'll just waste space for no reason. If you want to give it a try, substitute the `-m 1` to `-m 0` for **texconv**, and `dds:mipmaps=0` to `dds:mipmaps=1` for the **magick** commands below. Maybe this could help with performance or loading pop-in, if the engine has support for it, however they could also lead to unexpected side-effects, such as seams, visual blurring, shader oddities. I would advise against doing this, but it can be fun to experiment with. Still, do not add mipmap to every single image, that would be foolish. Prioritize the most used textures and most frequently visited areas, where you notice slower loading or model pop-in issues.

I would personally prefer to convert the DDS to PNG first, then edit the PNG files (as most image editors and apps can handle PNG files, unlike DDS). If you do not wish to convert them to PNG, that's fine, as you can spare yourself from an extra conversion process, though your image editor must be able to properly save in the DDS format.

Once you're done with the image editing, and if your images are in PNG, then you have to convert all the new files back to DDS with *texconv* in a directory (this assumes the command prompt is in where all your PNG files are).

For DXT5:

```
texconv -nologo -r -f DXT5 -srgb -m 1 -y *.png
```

For DXT1:

```
texconv -nologo -r -f DXT1 -srgb -m 1 -y *.png
```

You have to be careful that you either 1) use the same format as your source did for the image, *for images with transparency/alpha*, this is *DXT5*, and f*or normal images (without alpha/transparency)*, it would be *DXT1*. 2) You can also do this uncompressed, though this would heavily increase the filesize. If you don't want to bother knowing what format each original file had, then you should either use DXT5 for every file (even with those that have no alpha channel) or the uncompressed format. In any case, the repack script should warn you with a message if you change the original format to a different one.

Here is the uncompressed conversion:

```
texconv -nologo -r -f B8G8R8A8_UNORM -srgb -m 1 -y *.png
```

If you prefer ImageMagick, here are the commands for that too...

For DXT5 (if image has alpha channel):

```
magick mogrify -format dds -define dds:compression=dxt5 -define dds:mipmaps=0 *.png
```

For DXT1 (if image has no alpha):

```
magick mogrify -format dds -define dds:compression=dxt1 -define dds:mipmaps=0 *.png
```

For uncompressed format:

```
magick mogrify -format dds -define dds:compression=none -define dds:mipmaps=0 *.png
```

At this point, you should have the edited DDS files ready to be repacked. From my experience, because the colors can get washed out slightly (DXT compression artifacts), it's best to use the uncompressed format for fidelity, despite the bigger filesize. Also, if any PNG image gets darker or brighter in the DDS, use the `-srgb` parameter with *texconv*.

## Repacking regular G1T files

To repack a regular G1T file, you would use the *g1t_repack* script:

```
python g1t_repack.py <orig_file.g1t> <dds_dir> <output_file.g1t>
```

So first parameter is the original file, then the second is the directory that contains every replacement DDS file (also include the unchanged ones) in the format of four numeric values (like the extracted directory), and finally the output filename.

## Repacking a binary G1T file

For this, make sure each subdirectory has the new DDS file(s) in their respective folder, then use the *g1t_bin_repack* script:

```
g1t_bin_repack.py <dir> <output_file.bin>
```

Just make sure that the directory you use have the decompressed G1T files and the subfolders according to the extracted DDS files, i.e. `0000`, `0001` and so on.
