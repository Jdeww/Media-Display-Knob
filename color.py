from vibrant import Vibrant

v = Vibrant()

palette = v.get_palette('Thumbnail.jpg')

color = palette.dark_muted

print(color.rgb)