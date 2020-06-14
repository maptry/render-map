## Prerequisites

Install the following software to use this program:
- Python 3 [https://www.python.org/]
- Mapnik 3 [https://mapnik.org/]
- python-mapnik [https://github.com/mapnik/python-mapnik]

## Data Sources

The input data for this program is produced by the program from
the query-mapnik repository. Copy this file to `municipalities.json`.

Download the german municipality borders from
`https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/aktuell/vg250_01-01.utm32s.shape.ebenen.zip` and unzip it `unzip vg250_01-01.utm32s.shape.ebenen.zip`.

## Map Rendering

The program allows you to display the values of different attributes from
the JSON data file ("Population", "Area" or "PopulationDensity").

It also allows you to use specify the number of colors/shades to use and
how to map values to colors. For the color mapping you can use two
different algorithms:
- "quantiles" divides the entries into (roughly) equal sized sequences of entries
- "values" divides the maximum value with the number of colors

## Example

Then invoke 
`./render-map.py 100 quantiles PopulationDensity 2500 3500 municipalities.json vg250_2019-01-01.utm32s.shape.ebenen/vg250_ebenen/VG250_GEM.shp germany-population-density-by-1-percent-quantiles.png`
