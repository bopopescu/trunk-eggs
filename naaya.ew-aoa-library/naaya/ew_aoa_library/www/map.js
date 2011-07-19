(function() {

var M = window.M = {};

M.debug = true;
M.proj_wgs1984 = new OpenLayers.Projection("EPSG:4326");
M.map_projection = new OpenLayers.Projection("EPSG:900913");
M.project = function(point) {
  return point.clone().transform(M.proj_wgs1984, M.map_projection);
}

M.xyz_layer = function(name) {
  return new OpenLayers.Layer.XYZ(name,
    M.config['tiles_url'] + "/${z}/${x}/${y}.png",
    {'sphericalMercator': true, 'numZoomLevels': 7}
  );
}

M.add_view = function(tiles_layer) {
  var this_view = M.views[tiles_layer.name] = {};

  this_view.tiles_layer = tiles_layer;
  M.countries_map.addLayer(this_view.tiles_layer);

  this_view.polygons_layer = new OpenLayers.Layer.Vector(
    this_view.tiles_layer.name + ' - polygons',
    {displayInLayerSwitcher: false,
     visibility: false,
     styleMap: new OpenLayers.StyleMap({
      'default': new OpenLayers.Style({
        'fillOpacity': 0,
        'strokeOpacity': 0,
        'fontSize': 12,
        'fontWeight': 'bold',
        'label': "${count}"
      }),
      'select': new OpenLayers.Style({
        'fillOpacity': 0.4,
        'strokeOpacity': 0.1,
        'strokeWidth': 4
      })
    })});

  this_view.set_features = function(polygons_data) {
      $.each(polygons_data, function(n, poly) {
        poly.attributes['count'] = "";
      });
      this_view.polygons_layer.addFeatures(polygons_data);
      M.countries_map.addLayer(this_view.polygons_layer);
  };

  this_view.select_polygon = new OpenLayers.Control.SelectFeature(
    this_view.polygons_layer,
    {'multiple': true, 'toggle': true, 'clickout': false});
  this_view.select_polygon.handlers.feature.stopDown = false;
  M.countries_map.addControl(this_view.select_polygon);

  this_view.update_visibility = function() {
    var visibility = this_view.tiles_layer.getVisibility();
    this_view.polygons_layer.setVisibility(visibility);
    var select_control = this_view.select_polygon;
    if(this_view.tiles_layer.getVisibility()) {
      select_control.activate();
      select_control.unselectAll();
      M.current_view_name = this_view.tiles_layer.name;
      this_view.polygons_layer.redraw();
    } else {
      select_control.deactivate();
    }
  }

  this_view.update_document_counts = function(docs_and_countries) {
    $.each(this_view.polygons_layer.features, function(n, feature) {
      var count = 0;
      var feature_countries = feature.attributes['countries'];
      $.each(docs_and_countries, function(m, document_countries) {
        // for each document, see if any country matches this feature
        for(var i = 0; i < document_countries.length; i++) {
          var country = document_countries[i];
          if(feature_countries.indexOf(country) > -1) {
            // we have a match. count it and go to next document.
            count += 1;
            return;
          }
        }
      });
      if(! count) {
        count = "";
      }
      feature.attributes['count'] = count;
    });
    this_view.polygons_layer.redraw();
  };

  this_view.tiles_layer.events.on({
    'visibilitychanged': this_view.update_visibility
  });

  if(M.countries_map.baseLayer !== this_view.tiles_layer) {
    this_view.tiles_layer.setVisibility(false);
  }
  this_view.update_visibility();
}

M.get_current_view = function() {
  return M.views[M.current_view_name];
}

M.get_selected_countries = function() {
  var layer = M.get_current_view().polygons_layer;
  var countries = [];
  $.each(layer.selectedFeatures, function(n, feature) {
    $.merge(countries, feature.attributes['countries']);
  });
  return countries;
};

M.update_all_document_counts = function(docs_and_countries) {
  $.each(M.views, function(i, view) {
    view.update_document_counts(docs_and_countries);
  });
};

M.geojson_format = new OpenLayers.Format.GeoJSON({
  'internalProjection': M.map_projection,
  'externalProjection': M.proj_wgs1984
});

M.load_features = function(name, callback) {
  $.get(M.config['www_prefix'] + '/' + name, function(json_data) {
    callback(M.geojson_format.read(json_data));
  });
};

M.create_map_search = function(options) {
  M.countries_map = new OpenLayers.Map(options['map_div']);

  M.layer_switcher = new OpenLayers.Control.LayerSwitcher();
  M.countries_map.addControl(M.layer_switcher);
  $('.baseLbl', M.layer_switcher.layersDiv).text("Geographic level");
  M.layer_switcher.maximizeControl();

  M.views = {};
  M.add_view(M.xyz_layer("Country"));
  M.add_view(M.xyz_layer("Region"));


  M.countries_map.zoomToMaxExtent = function() {
    M.countries_map.setCenter(M.project(new OpenLayers.LonLat(35, 57)), 3);
  }
  M.countries_map.zoomToMaxExtent();

  M.load_features('countries.json', function(features) {
    var view = M.views["Country"];
    view.set_features(features);
    view.update_document_counts(M.config['docs_and_countries']);
  });

  M.load_features('regions.json', function(features) {
    var view = M.views["Region"];
    view.set_features(features);
    view.update_document_counts(M.config['docs_and_countries']);
  });
};

M.create_map_document = function(options) {
  M.document_map = new OpenLayers.Map(options['map_div'], {controls: []});
  M.document_map.addLayer(M.xyz_layer("Background"));
  M.document_map.setCenter(M.project(new OpenLayers.LonLat(30, 57)), 2);

  M.load_features('countries.json', function(features) {
    M.countries_layer = new OpenLayers.Layer.Vector(
      'Countries',
      {styleMap: new OpenLayers.StyleMap({
        'default': new OpenLayers.Style({
          'fillOpacity': 0.7,
          'fillColor': '#000',
          'strokeOpacity': 0
        })
      })});
    M.document_map.addLayer(M.countries_layer);

    var countries = M.config['document_countries'];
    $.each(features, function(n, country_poly) {
      if(countries.indexOf(country_poly['attributes']['name']) > -1) {
        M.countries_layer.addFeatures([country_poly]);
      }
    });
  });
};

})();
