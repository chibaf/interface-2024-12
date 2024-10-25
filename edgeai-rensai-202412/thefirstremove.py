from rembg import remove
from PIL import Image

def PutMargin(im, top, bottom, right, left):
    width, height = im.size
    height_new = height + top + bottom
    width_new= width + right + left
    res = Image.new(im.mode, (width_new, height_new), (0,0,0))
    res.paste(im, (left, top))
    return res

input = Image.open('nihonzaru_org.jpg')

input_1 = input.resize((200, 200))
input_2 = PutMargin(input_1, 100, 100, 100, 100)

output = remove(input_2)
output.save('bgremoved.png')

