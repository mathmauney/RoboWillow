class Geometry:
    """
    A geometry instance, as an object representation of GeoJSON's geometry dictinoary item,
    with some convenience methods.
    Attributes:

    - **type**: As specified when constructed
    - **coordinates**: As specified when constructed
    - **bbox**: If the bounding box wasn't specified when constructed then it is calculated on-the-fly.
    """
    def __init__(self, obj=None, type=None, coordinates=None, bbox=None):
        """
        Can be created from args, or without any to create an empty one from scratch.
        If obj isn't specified, type, coordinates, and optionally bbox can be set as arguments
        Parameters:

        - **obj**:
            Another geometry instance, an object with the \_\_geo_interface__ or a geojson dictionary of the Geometry type
        - **type** (optional):
            The type of geometry. Point, MultiPoint, LineString, MultiLineString,
            Polygon, or MultiPolygon.
        - **coordinates** (optional):
            A sequence of coordinates formatted according to the geometry type.
        - **bbox** (optional):
            The bounding box of the geometry as [xmin, ymin, xmax, ymax].
        """
        if isinstance(obj, Geometry):
            self._data = obj._data.copy()
        elif hasattr(obj, "__geo_interface__"):
            self._data = obj.__geo_interface__
        elif isinstance(obj, dict):
            self._data = obj
        elif type and coordinates:
            _data = {"type":type,"coordinates":coordinates}
            if bbox: _data.update({"bbox":bbox})
            self._data = _data
        else:
            # empty geometry dictionary
            self._data = {}

    def __setattr__(self, name, value):
        """Set a class attribute like obj.attr = value"""
        try: self._data[name] = value # all attribute setting will directly be redirected to adding or changing the geojson dictionary entries
        except AttributeError: self.__dict__[name] = value # except for first time when the _data attribute has to be set

    def __str__(self):
        if self.type == "Null":
            return "Geometry(type='Null')"
        else:
            return "Geometry(type=%s, coordinates=%s, bbox=%s)" % (self.type, self.coordinates, self.bbox)

    @property
    def __geo_interface__(self):
        return self._data.copy() if self._data else None

    # Attributes

    @property
    def type(self):
        return self._data["type"] if self._data else "Null"

    @type.setter
    def type(self, value):
        self._data["type"] = value

    @property
    def bbox(self):
        if self._data.get("bbox"): return self._data["bbox"]
        else:
            if self.type == "Null":
                raise Exception("Null geometries do not have bbox")
            elif self.type == "Point":
                x,y = self._data["coordinates"]
                return [x,y,x,y]
            elif self.type in ("MultiPoint","LineString"):
                coordsgen = (point for point in self._data["coordinates"])
            elif self.type == "MultiLineString":
                coordsgen = (point for line in self._data["coordinates"] for point in line)
            elif self.type == "Polygon":
                coordsgen = (point for point in self._data["coordinates"][0]) # only the first exterior polygon should matter for bbox, not any of the holes
            elif self.type == "MultiPolygon":
                coordsgen = (point for polygon in self._data["coordinates"] for point in polygon[0]) # only the first exterior polygon should matter for bbox, not any of the holes
            firstpoint = next(coordsgen)
            _xmin = _xmax = firstpoint[0]
            _ymin = _ymax = firstpoint[1]
            for _x,_y in coordsgen:
                if _x < _xmin: _xmin = _x
                elif _x > _xmax: _xmax = _x
                if _y < _ymin: _ymin = _y
                elif _y > _ymax: _ymax = _y
            return _xmin,_ymin,_xmax,_ymax

    @property
    def coordinates(self):
        return self._data["coordinates"]

    @coordinates.setter
    def coordinates(self, value):
        self._data["coordinates"] = value

    # Methods

    def update_bbox(self):
        """
        Removes any existing stored bbox attribute from the geojson dictionary.
        This way, until you set the bbox attribute again, the bbox will always
        be calculated on the fly and be up to date.
        Useful after making changes to the geometry coordinates.
        """
        if "bbox" in self._data:
            del self._data["bbox"]

    def validate(self, fixerrors=True):
        """
        Validates that the geometry is correctly formatted according to the geometry type.
        Parameters:
        - **fixerrors** (optional): Attempts to fix minor errors without raising exceptions (defaults to True)
        Returns:

        - True if the geometry is valid.
        Raises:
        - An Exception if not valid.
        """

        # validate nullgeometry or has type and coordinates keys
        if not self._data:
            # null geometry, no further checking needed
            return True
        elif "type" not in self._data or "coordinates" not in self._data:
            raise Exception("A geometry dictionary or instance must have the type and coordinates entries")

        # first validate geometry type
        if not self.type in ("Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon"):
            if fixerrors:
                coretype = self.type.lower().replace("multi","")
                if coretype == "point":
                    newtype = "Point"
                elif coretype == "linestring":
                    newtype = "LineString"
                elif coretype == "polygon":
                    newtype = "Polygon"
                else:
                    raise Exception('Invalid geometry type. Must be one of: "Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon"')

                if self.type.lower().startswith("multi"):
                    newtype = "Multi" + newtype

                self.type = newtype
            else:
                raise Exception('Invalid geometry type. Must be one of: "Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon"')

        # then validate coordinate data type
        coords = self._data["coordinates"]
        if not isinstance(coords, (list,tuple)): raise Exception("Coordinates must be a list or tuple type")

        # then validate coordinate structures
        if self.type == "Point":
            if not len(coords) == 2: raise Exception("Point must be one coordinate pair")
        elif self.type in ("MultiPoint","LineString"):
            if not len(coords) > 1: raise Exception("MultiPoint and LineString must have more than one coordinates")
        elif self.type == "MultiLineString":
            for line in coords:
                if not len(line) > 1: raise Exception("All LineStrings in a MultiLineString must have more than one coordinate")
        elif self.type == "Polygon":
            for exterior_or_holes in coords:
                if not len(exterior_or_holes) >= 3: raise Exception("The exterior and all holes in a Polygon must have at least 3 coordinates")
        elif self.type == "MultiPolygon":
            for eachmulti in coords:
                for exterior_or_holes in eachmulti:
                    if not len(exterior_or_holes) >= 3: raise Exception("The exterior and all holes in all Polygons of a MultiPolygon must have at least 3 coordinates")

        # validation successful
        return True
