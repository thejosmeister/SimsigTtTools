

# load categories file
cat_filename = 'default_charlwood_categories_map'

file_lines = []
f = open(f'{cat_filename}.yaml', 'r')
for file_line in f:
    file_lines.append(file_line)
f.close()

# find all lines to change
i = -1
line_nums_to_change = []
for line in file_lines:

    i += 1

    if line.find('id:') == -1:
        continue

    if line.find('A0000001') != -1:
        continue

    line_nums_to_change.append(i)

# change ids
_id = 2
for l in line_nums_to_change:
    file_lines[l] = f'  id: B{hex(_id)[2:].zfill(7).upper()}\n'

    _id += 1

# write to new file
with open(f'{cat_filename}v2.yaml', 'w') as file:
    for line in file_lines:
        file.write(line)
