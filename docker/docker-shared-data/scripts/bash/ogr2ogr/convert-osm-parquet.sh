SRC_DIR="/docker-shared-data/openstreetmap/maps/src"
OUT_DIR="/docker-shared-data/openstreetmap/maps/processed"

MAP_FILE_NAME="$1"
MAP_NAME="${1%%.*}"

if [ "$MAP_FILE_NAME" != $(basename $MAP_FILE_NAME) ]; then
    echo "Don't specify directory. The maps must be located in: $SRC_DIR."
    exit 1
fi

ogr2ogr \
    -if OSM \
    -f "Parquet" \
    -lco GEOMETRY=AS_WKT \
    "$OUT_DIR/$MAP_NAME" \
    "$SRC_DIR"/"$MAP_FILE_NAME"