#!/usr/bin/env python3

import mapnik
import json
import sys
import math
import collections

def clean_municipality_data(municipalities):
    # Clean up the data a bit:
    # 1. Make sure the every municipality appears only once in the data
    # 2. There are some entries with an abnormaly high population density.
    #    Manual inspection suggests this is because of a small area. I
    #    did not investigate further and the entries may actually be valid.
    #    But I decided to remove entries with small areas for now.
    # 3. I also removed entries with an area that is too large.
    # 4. There might be missing entries from the start because those
    #    were missing from wikidata or were missing the municipality key.
    # 5. There are still some entries with obviously wrong data. We
    #    leave them for now.
    data = {}
    for m in municipalities:
        if m['MunicipalityKey'] not in data:
            m['Area'] = float(m['Area'])
            if m['Area'] < 1.0 or m['Area'] > 900.0:
                continue
            m['Population'] = int(m['Population'])
            m['PopulationDensity'] = m['Population'] / m['Area']
            data[m['MunicipalityKey']] = m
    return list(data.values())

def load_municipality_data(filename):
    with open(filename) as f:
        data = json.load(f)
    return clean_municipality_data(data)

# Partition the color range by quantiles. We use 'num_buckets'
# colors and each color is used for
# (number of municipalities) / num_buckets
# places. Therefore each color represents the same number of
# municipalities.
def lower_border_quantiles(municipalities, attrib, num_buckets):
    values = sorted([m[attrib] for m in municipalities])
    bucket_size = math.ceil(len(values) / num_buckets)
    return [values[int(i*bucket_size)] for i in range(num_buckets)]

# Partition the color range by dividing the max value with 'num_buckets'
# Each color can represent very different numbers of municipalities.
# For example there are only very few large cities but many small towns.
def lower_border_max_value_divided(municipalities, attrib, num_buckets):
    max_value = max(m[attrib] for m in municipalities)
    borders = []
    i = 0.0
    print('max value: {}'.format(max_value))
    while max_value-i > 0.0000000001:
        borders.append(i)
        i += max_value/num_buckets
    return borders

class ColorMapping:
    def __init__(self, lower_borders):
        self.buckets = []
        self.stats = collections.defaultdict(int)
        for i, l in enumerate(lower_borders):
            p = mapnik.PolygonSymbolizer()
            c = 100.0 - i * 100.0 / len(lower_borders)
            p.fill = mapnik.Color('rgb({}%,0%,0%)'.format(c))
            p.gamma = 0.0
            self.buckets.append((l, p))

    def __getitem__(self, val):
        for l, p in self.buckets[-1::-1]:
            if val >= l:
                self.stats[l] += 1
                return p

    def print_key(self):
        print('the values are divided into {} different colors'.format(len(self.buckets)))
        lower_borders = [a for a, _ in self.buckets]
        for l, u in zip(lower_borders[:-1], lower_borders[1:]):
            print('{} <= value < {}: {}'.format(l, u, self.stats[l]))
        else:
            u, _ = self.buckets[-1]
            print('{} <= value: {}'.format(u, self.stats[u]))

color_functions = {
    'quantiles': lower_border_quantiles,
    'values': lower_border_max_value_divided,
}

def main(num_buckets, method, attrib, width, height, places_json, borders_shp, image):
    municipalities = load_municipality_data(places_json)

    if method in color_functions:
        borders = color_functions[method](municipalities, attrib, num_buckets)
    else:
        print('allowed are {}. you used "{}"'.format(color_functions.keys()), file=sys.stderr)
        sys.exit(1)
    color_mapping = ColorMapping(borders)

    map = mapnik.Map(width, height)
    map.background = mapnik.Color('lightgrey')

    # map each municipality to a color bucket
    style = mapnik.Style()
    for m in municipalities:
        # debugging
        #print('{}: {}'.format(m['Name'], m[attrib]))
        p = color_mapping[m[attrib]]
        if p is not None:
            r = mapnik.Rule()
            # AGS is an attribute in the shape file that contains the
            # official german municipality id. We compare it with the
            # municipality id we queried from wikidata. Since this is
            # an official id there is a good chance they will match.
            r.filter = mapnik.Expression("[AGS] = '{}'".format(m['MunicipalityKey']))
            r.symbols.append(p)
            style.rules.append(r)
        else:
            # no data available
            pass
    map.append_style('Municipalities', style)

    color_mapping.print_key()

    # tie everything together and render the image
    layer = mapnik.Layer('Country')
    layer.datasource = mapnik.Shapefile(file=borders_shp)
    layer.styles.append('Municipalities')
    map.layers.append(layer)
    map.zoom_all()
    mapnik.render_to_file(map, image)


if __name__ == '__main__':
    if len(sys.argv) != 9:
        print('usage: {} num_colors method attribute width height PLACES.json BORDERS.shp IMAGE.png'.format(sys.argv[0]), file=sys.stderr)
        print('num_colors: the number of colors/shades to use (1 - 100)')
        print('method: "quantiles" or "values"')
        print('attribute: one of "Population", "Area" or "PopulationDensity"', file=sys.stderr)
        sys.exit(1)
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6], sys.argv[7], sys.argv[8])
